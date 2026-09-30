# Claude Code config

Personal Claude Code setup, applied to `~/.claude` on any machine this repo is checked out on.

## Contents

- `CLAUDE.md` — global guidelines/instructions, linked to `~/.claude/CLAUDE.md`
- `settings.json` — the settings keys this repo owns (`outputStyle`, `statusLine`, `hooks.PreToolUse`); merged into `~/.claude/settings.json`, not overwritten
- `output-styles/plain.md` — "plain" output style (ASD-STE100 plain language, answer first)
- `statusline-command.sh` — status line: project/branch, model, context usage bar, session + daily cost, elapsed time
- `skills/commit/SKILL.md` — the `/commit` skill: drafts a commit message to a file and hands back `git commit -F <file>` instead of committing directly (see below)
- `danfault-plugins/` — a local Claude Code plugin marketplace (see below)
- `install.sh` — applies all of the above

## Install

```bash
./ai/claude/install.sh
```

It links `CLAUDE.md`, `output-styles/plain.md`, `statusline-command.sh`, and `skills/commit/SKILL.md` straight into `~/.claude/` (edits in the repo take effect immediately), and merges only the `outputStyle`/`statusLine`/`hooks` keys into `~/.claude/settings.json` — anything else already in that file (machine permissions, installed plugins, other hooks) is backed up and left alone; the `hooks.PreToolUse` list is merged entry-by-entry rather than replaced outright. It also registers the local plugin marketplace below.

Re-running it is safe.

## Commit safeguard

`skills/commit/SKILL.md` plus the `hooks.PreToolUse` entry in `settings.json` together mean Claude never runs `git commit` directly on this machine, in any repo. Instead, ask for `/commit` (or Claude reaches for it on its own): it drafts a commit message from the staged diff, writes it to `.git/claude-commit-message.txt`, and prints the exact `git commit -F <file>` command for you to run. The hook backs this up by hard-blocking any Bash command matching `git commit`, so it can't be bypassed by just running the command directly.

To remove it, delete the `git-commit-block` hook entry from `~/.claude/settings.json` (and re-run `install.sh`, or edit `settings.json` here so future installs don't bring it back).

## Plugin marketplace

`danfault-plugins/` is a self-contained Claude Code marketplace (`.claude-plugin/marketplace.json` + `plugins/`), added locally by `install.sh` via:

```bash
claude plugin marketplace add ai/claude/danfault-plugins
```

It ships two plugins:
- `introduce-me` — introduces a new topic in a fixed 4-section format
- `obsidian-vault` — capture notes, daily logs, session reports, project scaffolding, and reindexing for the Obsidian vault

Once added, install a plugin from a session with:

```
/plugin install <plugin-name>@danfault-plugins
```

## Verify

Start a new Claude Code session:
- The status line at the bottom shows project, branch, model, context bar, cost, elapsed time.
- Responses come back in plain language, answer first.
- `/plugin marketplace list` shows `danfault-plugins`; `/vault-help` (after installing `obsidian-vault`) confirms the plugin loads.

To change the output style later, run `/output-style` in a session.
