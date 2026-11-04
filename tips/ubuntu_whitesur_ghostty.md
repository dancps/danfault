# Ubuntu look: Ghostty + WhiteSur

Changes made on Ubuntu 24.04 (GNOME 46, X11) to make Ghostty and the desktop look closer to macOS. Written 2026-10-21.

## Ghostty

Config files are tracked in `terminal-configs/ghostty/` and linked into `~/.config/ghostty/` by `unix/setup.sh`.

| Setting | Why |
|---|---|
| `gtk-titlebar-style = tabs` | Puts the tabs inside the title bar, so there is one bar instead of two (like macOS). |
| `adjust-cell-height = -10%` | Less space between lines. Below about `-15%`, tall characters get cut. |
| `gtk-custom-css = ~/.config/ghostty/custom.css` | Loads `custom.css`: smaller tabs (24px), smaller tab text and close button, pill-shaped tab borders, brighter border on the active tab, no dividers between tabs, and small red, yellow and green window buttons. |

Reload the config with `Ctrl+Shift+,`. Title bar changes apply only to new windows.

Notes:

- With tabs in the title bar there is little empty space to drag the window. Hold `Super` and drag anywhere in the window (GNOME's `mouse-button-modifier`).
- `window-decoration = server` gives a GNOME-drawn title bar instead. Then `custom.css` cannot change the title bar, only the tab bar under it.
- Some of the empty space between commands comes from the zsh prompt (blank line + two-line prompt), not from Ghostty.

## WhiteSur theme

[WhiteSur](https://github.com/vinceliuice/WhiteSur-gtk-theme) is a macOS-like theme for GTK3, libadwaita (GTK4) and GNOME Shell. It is optional in the setup:

```bash
./unix/setup.sh --white-sur-theme
```

This step:

1. Installs `sassc`, `libglib2.0-dev-bin` (for `glib-compile-resources`) and `gnome-shell-extensions` (for User Themes).
2. Clones the repo to `~/Documents/projects/repos/WhiteSur-gtk-theme`. Keep this folder: its scripts are needed to uninstall.
3. Runs `./install.sh -l --shell -p 75`:
   - Themes go to `~/.themes` (Dark and Light, normal and solid).
   - `-l` writes the libadwaita override into `~/.config/gtk-4.0/` (Ghostty, Files, Settings). Do not run it with `sudo`.
   - `--shell -p 75` sets the top bar to 75% opacity (the highest the installer offers; default is 15%).
4. Sets the GTK3 theme and the GNOME Shell theme (User Themes extension) to `WhiteSur-Dark`.

Log out and in after installing so all apps pick up the theme.

### Changing options

There is no settings app. Run `./install.sh` again with new flags, and repeat every flag you want to keep (a missing flag goes back to its default). Useful flags: `-t blue` (accent), `-o solid` (no transparency), `-m` (Monterey style), `--darker`, `--round`, `--shell -h smaller` (thinner top bar), `--dialog` (choose with dialogs). After a reinstall, re-apply the shell theme (set the User Themes name to `''` and back) so GNOME reloads it.

For a fully solid top bar, change `rgba(0, 0, 0, 0.75)` to `1` in `#panel` in `~/.themes/WhiteSur-Dark/gnome-shell/gnome-shell.css`. The next `install.sh` run overwrites it.

`./tweaks.sh` covers other parts: `-d` (dock), `-f` (Firefox), `-F` (Flatpak), `-g` (login screen; needs `sudo`, not used here).

### Gotchas

- If User Themes is installed only in `~/.local/share/gnome-shell/extensions/`, `gsettings` fails with `No such schema`. Pass `--schemadir <extension>/schemas`, or install `gnome-shell-extensions` so the schema is system-wide.
- GTK4 apps read `~/.config/gtk-4.0` only when they start. A Ghostty process that started before the install keeps the old look until all its windows close, so test with `ghostty --gtk-single-instance=false`.
- With `gtk-titlebar-style = tabs`, Ghostty puts the window buttons inside the tab bar. WhiteSur styles them only under `headerbar windowcontrols`, so its buttons do not apply there, and its generic `button` style draws a grey square behind libadwaita's circle. `custom.css` removes the square and sets the colors itself.
- To compare the look without the override, rename `~/.config/gtk-4.0` and start a new process as above.
- Extensions that write to `~/.config/gtk-4.0` (for example Custom Accent Colors) overwrite the libadwaita override. Disable them.
- GNOME does not support theming libadwaita apps. A GNOME update can break the look.
- The installer also adds a `gnome-theme-switcher` app (switches the GTK4 variant).

### Uninstall

From the WhiteSur repo folder:

```bash
./install.sh -r                 # themes in ~/.themes and the ~/.config/gtk-4.0 override
./install.sh -r app             # gnome-theme-switcher app
gsettings set org.gnome.desktop.interface gtk-theme 'Yaru-purple-dark'
gsettings reset org.gnome.shell.extensions.user-theme name
```

`./install.sh -r` deletes `~/.config/gtk-4.0/gtk.css` without a backup. If a Flatpak override was added, undo it with `sudo flatpak override --reset`. Log out and in.
