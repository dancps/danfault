#!/usr/bin/env bash
#
# Restores terminal configs from this folder.
#   - iTerm2 (macOS): imports com.googlecode.iterm2.plist
#   - GNOME Terminal (Linux): loads gnome-terminal.dconf into dconf
# Quit iTerm2 before running so it doesn't overwrite the import on exit.

set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- iTerm2 ---------------------------------------------------------------
ITERM_PLIST="$SRC/com.googlecode.iterm2.plist"
if command -v defaults >/dev/null 2>&1 && [ -f "$ITERM_PLIST" ]; then
  echo "==> Restoring iTerm2 prefs"
  defaults import com.googlecode.iterm2 "$ITERM_PLIST"
  killall cfprefsd >/dev/null 2>&1 || true
  echo "    Imported. Restart iTerm2 (or log out/in) to see changes."
else
  echo "==> No iTerm2 backup to restore, skipping"
fi

# --- GNOME Terminal -------------------------------------------------------
GNOME_DCONF="$SRC/gnome-terminal.dconf"
if command -v dconf >/dev/null 2>&1 && [ -f "$GNOME_DCONF" ]; then
  echo "==> Restoring GNOME Terminal settings"
  dconf load /org/gnome/terminal/ < "$GNOME_DCONF"
  echo "    Loaded. Open a new GNOME Terminal window to see changes."
else
  echo "==> No GNOME Terminal backup to restore, skipping"
fi

echo "Done."
