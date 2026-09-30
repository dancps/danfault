#!/usr/bin/env bash

input=$(cat)

# Extract fields
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // .workspace.current_dir // ""')
model_id=$(echo "$input" | jq -r '.model.id // ""')
model=$(echo "$input" | jq -r '.model.display_name // ""')
pre_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')
transcript_path=$(echo "$input" | jq -r '.transcript_path // ""')
total_input=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_output=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
cache_write=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')

# Context usage %: compute from raw token counts against the actual window size.
# This is robust against CC reporting used_percentage against the wrong denominator
# (e.g. 200k instead of the real 1M window on extended-context models). Falls back to
# CC's pre-calculated value only when raw counts are unavailable (e.g. early in session).
used_pct=""
if [ "$total_input" -gt 0 ] 2>/dev/null && [ "$ctx_size" -gt 0 ] 2>/dev/null; then
  used_pct=$(awk -v ti="$total_input" -v cs="$ctx_size" 'BEGIN { printf "%.0f", (ti/cs)*100 }')
elif [ -n "$pre_pct" ]; then
  used_pct="$pre_pct"
fi

# Project name: basename of project_dir
project_name=$(basename "$project_dir")

# Git branch + worktree detection (skip optional locks)
#
# Ask git rather than testing for a .git directory: in a linked worktree `.git` is a FILE
# containing "gitdir: ...", so `[ -d "$dir/.git" ]` is false and branch detection silently
# skipped. A worktree is where you most want to see the branch.
branch=""
worktree_name=""
repo_name="$project_name"
if [ -n "$project_dir" ] && GIT_OPTIONAL_LOCKS=0 git -C "$project_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  g() { GIT_OPTIONAL_LOCKS=0 git -C "$project_dir" "$@" 2>/dev/null; }

  # Branch, falling back to a short SHA when HEAD is detached (symbolic-ref fails there,
  # which would blank the segment the same way the .git test used to).
  branch=$(g symbolic-ref --short HEAD)
  [ -z "$branch" ] && { sha=$(g rev-parse --short HEAD); [ -n "$sha" ] && branch="@$sha"; }

  # In the main checkout git-dir == git-common-dir; in a linked worktree the git-dir is
  # .git/worktrees/<name> while the common dir stays .git, so they differ.
  gitdir=$(g rev-parse --path-format=absolute --git-dir)
  common=$(g rev-parse --path-format=absolute --git-common-dir)
  if [ -n "$common" ] && [ -n "$gitdir" ] && [ "$common" != "$gitdir" ]; then
    repo_name=$(basename "$(dirname "$common")")          # the main repo, e.g. itaipu
    worktree_name=$(basename "$(g rev-parse --show-toplevel)")
  fi
fi

# Build progress bar (10 chars wide, heavy/light rule style, color-coded by pct)
bar=""
if [ -n "$used_pct" ]; then
  total=10
  filled=$(echo "$used_pct $total" | awk '{printf "%d", ($1/100)*$2 + 0.5}')
  empty=$((total - filled))
  bar_filled=$(printf '%0.s━' $(seq 1 $filled) 2>/dev/null || python3 -c "print('━'*$filled)")
  bar_empty=$(printf '%0.s─' $(seq 1 $empty) 2>/dev/null || python3 -c "print('─'*$empty)")

  # Color thresholds: green <50%, yellow 50-80%, red >80%
  # $'...' (ANSI-C quoting) resolves the escapes at assignment time, so the
  # final printf can stay a plain %s and never has to reinterpret text.
  if awk -v p="$used_pct" 'BEGIN { exit !(p+0 > 80) }'; then
    color=$'\033[31m'
  elif awk -v p="$used_pct" 'BEGIN { exit !(p+0 >= 50) }'; then
    color=$'\033[33m'
  else
    color=$'\033[32m'
  fi
  reset=$'\033[0m'

  bar="${color}${bar_filled}${bar_empty} ${used_pct}%${reset}"
fi

# Token cost estimate
# Pricing per million tokens (Anthropic public pricing)
# claude-opus-4 / claude-opus-4-5: input $15, output $75, cache_write $18.75, cache_read $1.50
# claude-sonnet-4 / sonnet-4-5:    input $3,  output $15, cache_write $3.75,  cache_read $0.30
# claude-haiku-3-5:                 input $0.80, output $4, cache_write $1,    cache_read $0.08
session_cost_raw=0
cost_str=""
if [ "$total_input" -gt 0 ] || [ "$total_output" -gt 0 ] 2>/dev/null; then
  session_cost_raw=$(echo "$model_id $total_input $total_output $cache_write $cache_read" | awk '{
    mid=$1; ti=$2; to=$3; cw=$4; cr=$5
    in_price=3; out_price=15; cw_price=3.75; cr_price=0.30
    if (mid ~ /opus/) {
      in_price=15; out_price=75; cw_price=18.75; cr_price=1.50
    } else if (mid ~ /haiku/) {
      in_price=0.80; out_price=4; cw_price=1; cr_price=0.08
    }
    printf "%.6f", (ti/1000000)*in_price + (to/1000000)*out_price + (cw/1000000)*cw_price + (cr/1000000)*cr_price
  }')
  cost_str=$(awk -v c="$session_cost_raw" 'BEGIN { if (c < 0.01) printf "$0.00"; else printf "$%.2f", c }')
fi

# Daily cost: sum completed sessions from log, add current session
daily_str=""
today=$(date "+%Y-%m-%d")
costs_file="$HOME/.claude/costs/$today.jsonl"
if [ -f "$costs_file" ]; then
  past_total=$(jq -rs --arg t "$transcript_path" \
    '[.[] | select(.transcript != $t) | .cost] | add // 0 | . * 1000000 | round / 1000000' \
    "$costs_file" 2>/dev/null || echo "0")
  session_count=$(jq -rs --arg t "$transcript_path" \
    '[.[] | select(.transcript != $t)] | length' \
    "$costs_file" 2>/dev/null || echo "0")
  daily_total=$(awk -v p="$past_total" -v s="$session_cost_raw" 'BEGIN { printf "%.6f", p+s }')
  daily_count=$(( session_count + 1 ))
  daily_str=$(awk -v d="$daily_total" -v n="$daily_count" \
    'BEGIN { if (d < 0.01) printf "$0.00 day (%d)", n; else printf "$%.2f day (%d)", d, n }')
fi

# Session elapsed time from transcript file
elapsed_str=""
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  first_ts=$(grep -m1 '"timestamp"' "$transcript_path" 2>/dev/null | sed 's/.*"timestamp"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
  if [ -n "$first_ts" ]; then
    # Convert ISO 8601 UTC timestamp to epoch seconds
    # The timestamp ends with Z (UTC), so we must parse it as UTC
    ts_stripped="${first_ts%%.*}"
    start_epoch=$(TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%S" "$ts_stripped" "+%s" 2>/dev/null \
      || date -ud "$first_ts" "+%s" 2>/dev/null \
      || date -d "$first_ts" "+%s" 2>/dev/null)
    if [ -n "$start_epoch" ]; then
      now_epoch=$(date "+%s")
      diff=$(( now_epoch - start_epoch ))
      hours=$(( diff / 3600 ))
      mins=$(( (diff % 3600) / 60 ))
      secs=$(( diff % 60 ))
      if [ "$hours" -gt 0 ]; then
        elapsed_str=$(printf "%dh%02dm" "$hours" "$mins")
      else
        elapsed_str=$(printf "%dm%02ds" "$mins" "$secs")
      fi
    fi
  fi
fi

# Assemble parts
parts=()
# In a worktree show both: which repo, and which worktree of it.
if [ -n "$worktree_name" ]; then
  parts+=("⌂ $repo_name ⑂ $worktree_name")
elif [ -n "$project_name" ]; then
  parts+=("⌂ $project_name")
fi
[ -n "$branch" ] && parts+=("⎇ $branch")
[ -n "$model" ] && parts+=("$model")
[ -n "$bar" ] && parts+=("$bar")
[ -n "$cost_str" ] && parts+=("$cost_str")
[ -n "$daily_str" ] && parts+=("$daily_str")
[ -n "$elapsed_str" ] && parts+=("$elapsed_str")

# Join with separator (single middle dot, decluttered vs. the old "  |  ")
result=""
for part in "${parts[@]}"; do
  if [ -z "$result" ]; then
    result="$part"
  else
    result="$result · $part"
  fi
done

printf '%s' "$result"
