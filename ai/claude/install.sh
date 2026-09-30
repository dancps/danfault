#!/usr/bin/env bash
# Applies the ai/claude config bundle to this machine's ~/.claude.
# Safe to re-run. Never overwrites an existing file blindly — anything
# already there gets backed up, then you're asked before it's replaced.
set -e

INSTALL_FILE=$(readlink -f "$0")
CLAUDE_DIR=$(dirname "$INSTALL_FILE")

TARGET="$HOME/.claude"
mkdir -p "$TARGET/output-styles" "$TARGET/skills/commit"

# Symlink $1 (repo file) to $2 (target in ~/.claude), so edits in the repo
# take effect immediately. If something is already at the target:
#   - if it's already the right symlink, leave it alone (idempotent reruns)
#   - otherwise back it up, then ask before overwriting
link_with_confirm() {
  local src="$1" dst="$2"

  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "Already linked: $dst"
    return
  fi

  if [ -e "$dst" ] || [ -L "$dst" ]; then
    local backup="${dst}.bak-$(date +%Y%m%d%H%M%S)"
    cp -a "$dst" "$backup"
    echo "Backed up $dst to $backup"

    read -r -p "Overwrite $dst with a link to $src? [y/N] " reply
    case "$reply" in
      [yY]|[yY][eE][sS]) ;;
      *) echo "Skipped $dst"; return ;;
    esac
  fi

  ln -sf "$src" "$dst"
  echo "Linked $dst -> $src"
}

link_with_confirm "$CLAUDE_DIR/CLAUDE.md" "$TARGET/CLAUDE.md"
link_with_confirm "$CLAUDE_DIR/output-styles/plain.md" "$TARGET/output-styles/plain.md"
link_with_confirm "$CLAUDE_DIR/statusline-command.sh" "$TARGET/statusline-command.sh"
link_with_confirm "$CLAUDE_DIR/skills/commit/SKILL.md" "$TARGET/skills/commit/SKILL.md"
chmod +x "$CLAUDE_DIR/statusline-command.sh"

# settings.json holds machine-specific permissions/plugins/hooks too, so it
# is never symlinked wholesale. Merge in just the keys from this repo's
# settings.json, backing up whatever was there first. "hooks" is merged one
# level deeper (per event type, deduping identical entries) so this doesn't
# clobber unrelated hooks already configured on the machine.
SETTINGS="$TARGET/settings.json"
if command -v python3 >/dev/null 2>&1; then
  python3 - "$CLAUDE_DIR/settings.json" "$SETTINGS" <<'PY'
import json, sys, pathlib, datetime

src_path, dst_path = sys.argv[1], sys.argv[2]
src = json.loads(pathlib.Path(src_path).read_text())

dst_file = pathlib.Path(dst_path)
dst = json.loads(dst_file.read_text()) if dst_file.exists() else {}

if dst_file.exists():
    backup = dst_file.with_suffix(f".json.bak-{datetime.datetime.now():%Y%m%d%H%M%S}")
    backup.write_text(dst_file.read_text())
    print(f"Backed up existing settings.json to {backup}")

for key, value in src.items():
    if key == "hooks" and isinstance(value, dict) and isinstance(dst.get(key), dict):
        for event, hook_list in value.items():
            existing = dst[key].setdefault(event, [])
            for entry in hook_list:
                if entry not in existing:
                    existing.append(entry)
    else:
        dst[key] = value

dst_file.write_text(json.dumps(dst, indent=2) + "\n")
print(f"Merged {list(src.keys())} into {dst_path}")
PY
else
  echo "python3 not found — merge these keys into $SETTINGS by hand:"
  cat "$CLAUDE_DIR/settings.json"
fi

# Register the personal plugin marketplace (no-op if already added).
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace add "$CLAUDE_DIR/danfault-plugins" 2>&1 || true
else
  echo "claude CLI not found on PATH — add the marketplace manually later with:"
  echo "  claude plugin marketplace add \"$CLAUDE_DIR/danfault-plugins\""
fi

echo "Done. Start a new Claude Code session to pick up the changes."
