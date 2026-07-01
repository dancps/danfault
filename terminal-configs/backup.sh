#!/usr/bin/env bash
#
# Backs up terminal configs into this folder so they can be version-controlled.
#   - iTerm2 (macOS): exports com.googlecode.iterm2.plist
#   - GNOME Terminal (Linux): dumps /org/gnome/terminal/ from dconf
# Whichever isn't available on this machine is skipped.

set -euo pipefail

DEST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- iTerm2 ---------------------------------------------------------------
if command -v defaults >/dev/null 2>&1 && \
   defaults read com.googlecode.iterm2 >/dev/null 2>&1; then
  echo "==> Backing up iTerm2 prefs"
  # iTerm caches prefs in memory; flush them so the export isn't stale.
  killall cfprefsd >/dev/null 2>&1 || true
  defaults export com.googlecode.iterm2 "$DEST/com.googlecode.iterm2.plist"
  echo "    -> $DEST/com.googlecode.iterm2.plist"
else
  echo "==> iTerm2 not found, skipping"
fi

# --- GNOME Terminal -------------------------------------------------------
if command -v dconf >/dev/null 2>&1 && \
   dconf list /org/gnome/terminal/ >/dev/null 2>&1; then
  echo "==> Backing up GNOME Terminal settings"
  dconf dump /org/gnome/terminal/ > "$DEST/gnome-terminal.dconf"
  echo "    -> $DEST/gnome-terminal.dconf"
else
  echo "==> GNOME Terminal not found, skipping"
fi

echo "Done. Commit the changes in $DEST to save them."
