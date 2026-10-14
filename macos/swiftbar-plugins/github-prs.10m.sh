#!/bin/bash
# <bitbar.title>GitHub PR Tracker</bitbar.title>
# <bitbar.version>1.0</bitbar.version>
# <bitbar.author>Danilo Calhes</bitbar.author>
# <bitbar.author.github>dcalhes</bitbar.author.github>
# <bitbar.desc>Shows your open GitHub pull requests, using the authenticated `gh` CLI session.</bitbar.desc>

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

PLUGIN_DIR="$(cd "$(dirname "$0")" && pwd)"
ICON_PATH="$PLUGIN_DIR/icon.png"
ICON_BASE64=""
[ -f "$ICON_PATH" ] && ICON_BASE64=$(base64 < "$ICON_PATH" | tr -d '\n')

STATE_DIR="$HOME/Library/Application Support/github-pr-tracker"
STATE_FILE="$STATE_DIR/state"
mkdir -p "$STATE_DIR"
[ -f "$STATE_FILE" ] || echo "include_review=false" > "$STATE_FILE"
# shellcheck source=/dev/null
source "$STATE_FILE"

if [ "$1" = "toggle" ]; then
  if [ "$include_review" = "true" ]; then
    echo "include_review=false" > "$STATE_FILE"
  else
    echo "include_review=true" > "$STATE_FILE"
  fi
  exit 0
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh not found"
  echo "---"
  echo "Install: brew install gh | color=red"
  exit 0
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "⚠️ gh not authenticated"
  echo "---"
  echo "Run: gh auth login | color=red"
  exit 0
fi

render_prs() {
  jq -r '.[] | "--\(.repository.nameWithOwner) #\(.number): \(.title | gsub("\\|"; "-")) | href=\(.url)"'
}

authored_json=$(gh search prs --author=@me --state=open --json repository,number,title,url,updatedAt 2>/dev/null)
authored_count=$(echo "$authored_json" | jq 'length')

review_count=0
review_json="[]"
if [ "$include_review" = "true" ]; then
  review_json=$(gh search prs --review-requested=@me --state=open --json repository,number,title,url,updatedAt 2>/dev/null)
  review_count=$(echo "$review_json" | jq 'length')
fi

total=$((authored_count + review_count))
label="$total"
[ "$total" -eq 0 ] && label=""
if [ -n "$ICON_BASE64" ]; then
  echo "$label | image=$ICON_BASE64"
else
  echo "🐙 $label"
fi

echo "---"
echo "Authored ($authored_count)"
if [ "$authored_count" -gt 0 ]; then
  echo "$authored_json" | render_prs
else
  echo "--No open PRs"
fi

if [ "$include_review" = "true" ]; then
  echo "---"
  echo "Review requested ($review_count)"
  if [ "$review_count" -gt 0 ]; then
    echo "$review_json" | render_prs
  else
    echo "--No open PRs"
  fi
  echo "---"
  echo "Hide review-requested PRs | bash='$0' param1=toggle terminal=false refresh=true"
else
  echo "---"
  echo "Show review-requested PRs | bash='$0' param1=toggle terminal=false refresh=true"
fi

echo "---"
echo "Refresh | refresh=true"
