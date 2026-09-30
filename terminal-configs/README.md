# terminal-configs

Version-controlled backups of terminal settings (themes, profiles, colors,
keybindings, fonts).

- **iTerm2** (macOS) — stored as `com.googlecode.iterm2.plist`
- **GNOME Terminal** (Linux) — stored as `gnome-terminal.dconf`

Each script auto-detects what's available on the current machine and skips the
other terminal, so the same folder works on both macOS and Linux.

## Usage

```bash
cd terminal-configs

# Save current settings into this folder, then commit them
./backup.sh
git add . && git commit -m "backup terminal configs"

# Restore settings on a new/clean machine after cloning
./restore.sh
```

## Notes

- **`backup.sh`** flushes iTerm2's in-memory prefs (`killall cfprefsd`) before
  exporting so the saved plist isn't stale.
- **Quit iTerm2 before running `restore.sh`** — otherwise iTerm overwrites the
  freshly imported prefs when it exits.
- After restoring: restart iTerm2 (or log out/in) and open a new GNOME Terminal
  window to see the changes.

## Just the iTerm2 color scheme

To export only the palette (not full prefs):
`Settings → Profiles → Colors → Color Presets → Export…` → produces a
`.itermcolors` file you can drop in here too.
