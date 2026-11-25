---
name: vault-git-setup
description: Set up git backup for an Obsidian vault — .gitignore, secret scan, private GitHub repo, first commit, and the Obsidian Git plugin settings — or attach another machine's copy of the vault to the existing repo. Asks before every operation.
user-invocable: true
---

# Skill: Vault Git Setup

Version a vault in a private GitHub repo and keep it in sync with the Obsidian Git plugin. Reference: `docs/vault-git-backup.md` in the danfault repo.

## Usage
```
/obsidian-vault:vault-git-setup            # default vault
/obsidian-vault:vault-git-setup <vault>    # vault name from vault.yaml
```

## Rules

- **Ask before every operation that changes something.** This includes writing a file, `git init`/`add`/`remote`/`push`, `gh repo create`, and changing plugin settings. Show the exact command or file content first, and wait for a yes. Read-only checks (status, sizes, scans) do not need a question.
- Never run `git commit`. Write the message to `<vault>/.git/claude-commit-message.txt` and give the user `git commit -F .git/claude-commit-message.txt` to run. Do not put the draft in the vault's working tree, because Obsidian Sync would upload it.
- Never delete vault files. To keep something out of git, propose a `.gitignore` entry.
- The repo must be private. Never push a vault to a public repo.

## Instructions

1. **Find the vault and its state** (read-only):
   ```bash
   V=$(danfault vault path [--vault <name>])
   git -C "$V" status -sb; git -C "$V" remote -v
   ls -a "$V" "$V/.obsidian" "$V/.obsidian/plugins" 2>/dev/null
   ```
   Then choose the path:
   - The vault has no remote, and the repo does not exist on GitHub → **First machine** (step 2).
   - The repo exists and this machine's vault has no `.git` → **Another machine** (step 8).
   - Both are already set up → go to step 6 to check the plugin.

### First machine

2. **`.gitignore`** — if it is missing, propose this content and ask before writing:
   ```gitignore
   .obsidian/workspace*.json
   .obsidian/cache
   .trash/
   04-archive/feedbacks/
   ```
   Ask whether other folders are sensitive or too large to version.

3. **Scan before the first commit** (read-only):
   ```bash
   cd "$V" && uvx -q detect-secrets scan --all-files --exclude-files '^\.git/' .
   find . -path ./.git -prune -o -type f -size +50M -print
   du -sh --exclude=.git .
   ```
   Report the findings. Hits inside ignored files (for example pane ids in `workspace.json`) are not a problem. Stop if a real secret or a file over 100 MB would be committed.

4. **Repo** — confirm the owner (`gh api user --jq .login`). The default repo name is `<vault>-obsidian-vault`. Ask before running:
   ```bash
   danfault vault init <vault> --path "$V" --github
   ```
   This adds the `.gitignore` if it is missing, runs `git init -b main`, creates the private repo and adds `origin` over SSH. It skips the steps that are already done and never commits. If the user wants another repo name, run the commands by hand instead:
   ```bash
   gh repo create <name> --private
   git -C "$V" init -b main      # only if there is no .git
   git -C "$V" remote add origin git@github.com:<owner>/<name>.git
   ```

5. **First commit** — ask before `git -C "$V" add -A`. Show `git status --short | wc -l` and any paths that look sensitive. Draft the message in `.git/claude-commit-message.txt` and give the user the command:
   ```bash
   cd "$V" && git commit -F .git/claude-commit-message.txt && git push -u origin main
   ```

### Plugin (both machines)

6. **Obsidian Git plugin** — check `$V/.obsidian/plugins/obsidian-git/` and `community-plugins.json`. If the plugin is missing, ask the user to install it: *Settings → Community plugins → Browse → "Git" (Vinzent03)*, then close Obsidian.

7. **Settings** — check that Obsidian is closed (`pgrep -fa obsidian` shows no app process; MCP servers do not count). If it is open, ask the user to close it, because Obsidian overwrites `data.json` on exit. Show the settings and ask before writing `$V/.obsidian/plugins/obsidian-git/data.json`. If the file exists, merge these keys into it instead of replacing it:
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
   If Obsidian is a Flatpak (`flatpak info md.obsidian.Obsidian`), check that the sandbox reaches the remote (read-only):
   ```bash
   flatpak run --command=sh md.obsidian.Obsidian -c "cd '$V' && git ls-remote origin HEAD"
   ```
   Then tell the user to open Obsidian and run **Git: Commit-and-sync** once, and to check the commit on GitHub.

### Another machine

8. **Attach without overwriting notes** — the notes may already be there through Obsidian Sync. Show these commands and ask before running each step:
   ```bash
   cd "$V"
   git clone --no-checkout git@github.com:<owner>/<name>.git /tmp/vault-git
   mv /tmp/vault-git/.git . && git reset
   git ls-files --deleted -z | xargs -0 git restore --
   git status
   ```
   Show `git status` to the user. Modified notes are local versions that differ from the repo. Ask the user how to handle them before the plugin commits them. Then go to step 6. The plugin and its settings come with the repo, so the user only needs to enable the plugin.
