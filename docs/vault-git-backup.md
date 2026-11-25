# Vault backup with git

Obsidian Sync skips files that are not notes or media (for example `project.json`) unless "Sync all other types" is on. It also never syncs dot-files (`.indexignore`, `.gitkeep`). We version the vault in a private GitHub repo instead, with the Obsidian Git community plugin. Obsidian Sync can stay on for live sync of notes; git carries everything else and keeps history.

Use `/obsidian-vault:vault-git-setup` to do this setup. It asks before each operation.

`danfault vault init NAME --path DIR --github` does steps 1 and 3 in one command. It writes a basic `.gitignore`, runs `git init -b main`, creates the private repo `NAME-obsidian-vault` and adds it as `origin` over SSH. It skips what already exists and never commits.

## Setup (first machine)

1. **`.gitignore`** at the vault root:
   ```gitignore
   .obsidian/workspace*.json
   .obsidian/cache
   .trash/
   04-archive/feedbacks/
   ```
   `workspace*.json` is per-device UI state and causes conflicts between machines.
2. **Secret scan** before the first commit: `uvx detect-secrets scan --all-files --exclude-files '^\.git/' .`. Check for files over 100 MB (the GitHub limit).
3. **Private repo:** `gh repo create <name> --private`, then `git remote add origin git@github.com:<owner>/<name>.git`.
4. **First commit and push** (`git push -u origin main`).
5. **Obsidian Git plugin** (Vinzent03): install it from *Settings → Community plugins*. Write the settings while Obsidian is closed, or Obsidian overwrites them.

## Plugin settings

`.obsidian/plugins/obsidian-git/data.json` (merged with the plugin defaults):

```json
{
  "commitMessage": "vault backup: {{date}} ({{hostname}})",
  "autoCommitMessage": "vault backup: {{date}} ({{hostname}})",
  "autoSaveInterval": 10,
  "autoBackupAfterFileChange": true,
  "autoPullInterval": 10,
  "autoPullOnBoot": true,
  "pullBeforePush": true,
  "syncMethod": "merge",
  "disablePopupsForNoChanges": true,
  "showStatusBar": true
}
```

The plugin commits and pushes 10 minutes after the last edit. It also pulls every 10 minutes and on startup. `{{hostname}}` shows which machine made each commit.

## Flatpak Obsidian

The Flatpak (`md.obsidian.Obsidian`) has its own `git` and uses the host's `~/.ssh` and ssh-agent. To check that the sandbox can reach the remote:

```bash
flatpak run --command=sh md.obsidian.Obsidian -c "cd <vault> && git ls-remote origin HEAD"
```

## Another machine

The vault may already be there through Obsidian Sync, without the JSON and dot-files. To attach it to the repo without overwriting notes:

```bash
cd <vault>
git clone --no-checkout git@github.com:<owner>/<name>.git /tmp/vault-git
mv /tmp/vault-git/.git . && git reset                   # index = repo, working tree untouched
git ls-files --deleted -z | xargs -0 git restore --     # bring back only the missing files
git status                                              # review notes that differ before the plugin commits them
```

The plugin and its settings come with the repo. Enable the plugin in *Settings → Community plugins*.
