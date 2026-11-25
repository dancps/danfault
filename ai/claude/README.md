# Claude Code config

Personal Claude Code setup, applied to `~/.claude` on any machine this repo is checked out on.

## Contents

- `CLAUDE.md` — global guidelines/instructions, linked to `~/.claude/CLAUDE.md`
- `settings.json` — the settings keys this repo owns (`outputStyle`, `statusLine`, `hooks.PreToolUse`, `hooks.PostToolUse`); merged into `~/.claude/settings.json`, not overwritten
- `output-styles/plain.md` — "plain" output style (ASD-STE100 plain language, answer first)
- `statusline-command.sh` — status line: project/branch, model, context usage bar, session + daily cost, elapsed time
- `skills/commit/SKILL.md` — the `/commit` skill: commits the staged change with a single-line message focused on why, with no Claude attribution (see below)
- `danfault-plugins/` — a local Claude Code plugin marketplace (see below)
- `install.sh` — applies all of the above

## Install

```bash
./ai/claude/install.sh
```

It links `CLAUDE.md`, `output-styles/plain.md`, `statusline-command.sh`, and `skills/commit/SKILL.md` straight into `~/.claude/` (edits in the repo take effect immediately), and merges only the `outputStyle`/`statusLine`/`hooks` keys into `~/.claude/settings.json` — anything else already in that file (machine permissions, installed plugins, other hooks) is backed up and left alone; each `hooks` event list is merged entry-by-entry rather than replaced outright. It also registers the local plugin marketplace below.

Re-running it is safe. When a target file already exists (and isn't already the right link), it asks before replacing it and keeps a `<file>.bak-<timestamp>` backup of anything it replaces. Answering no leaves the file untouched, with no backup.

### Non-interactive install

From a script (provisioning, dotfiles bootstrap, CI), pass `--yes`:

```bash
./ai/claude/install.sh --yes
```

Every conflicting file is backed up to `<file>.bak-<timestamp>` and then replaced — nothing is asked and nothing is lost. Without `--yes` and without a terminal, conflicting files are skipped (with a message) instead of failing the run.

## Commit format

Claude commits directly (the old `git-commit-block` hook was removed on 2026-11-25). `skills/commit/SKILL.md` and `CLAUDE.md` fix the format: one line, focused on why, no body, and no Claude attribution (no `Co-Authored-By`, no "Generated with Claude Code", no session link). Commits to the default branch need the user's say-so. To hide Claude Code's own attribution, set `"attribution": {"commit": "", "pr": "", "sessionUrl": false}` in `~/.claude/settings.json` (`install.sh` does not merge that key).

## Vault reindex hook

The `hooks.PostToolUse` entry (`# danfault:vault-reindex`) runs after every `Write` or `Edit`. If the edited file is a note inside a vault registered in `~/.config/danfault/vault.yaml`, it reindexes that vault in the background with `obsidian-index --for-file`, so `obsidian_search` sees the change. Edits outside every vault do nothing.

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
- `/plugin marketplace list` shows `danfault-plugins`; `/obsidian-vault:vault-help` (after installing `obsidian-vault`) confirms the plugin loads.

To change the output style later, run `/output-style` in a session.
