# Vault projects and tasks

`danfault vault` reads project-management data from an Obsidian vault without changing how the vault is organized.

## Commands

```
danfault vault list projects [--status S]
danfault vault tasks [--project P] [--status S]
danfault vault project init P [--title T] [--domain D] [--goal G] [--status S]
danfault vault project set-status P S
danfault vault project link P [--repo owner/repo]
danfault vault task set-status P T S
danfault vault which
danfault vault health-check [--project P]
```

## Decision: infer from the folder layout, store CLI metadata in JSON

- A project is a folder in `01-projects/`. A task is a note in `01-projects/<project>/tasks/`.
- The CLI never edits `SUMMARY.md` or task notes (`project init` only creates a missing `SUMMARY.md`). No migration is needed: notes without a status show `unknown`.
- Metadata the CLI writes goes to an optional `01-projects/<project>/project.json`. When `project.json` has a field, it wins over the `SUMMARY.md` frontmatter.
- Status is free text. There is no fixed vocabulary.
- Task statuses follow the same rule: `task set-status` writes `"tasks": {"<task id>": "<status>"}` in the project's `project.json`, which wins over the task's frontmatter.
- When `project.json` and a note disagree, the commands print a warning to stderr. `set-status` reminds you to update the note. `health-check` lists every divergence (and `tasks` entries without a note) and exits 1.

## Decision: pick the vault from the current repo, through project.json

A code repo is linked to a project in the vault, not the other way round: `project link` adds the repo's `owner/repo` (from `git remote get-url origin`) to `repos` in the project's `project.json`. Nothing is written to the code repo, so this works in repos shared with other people, and the link travels with the vault's git repo to every machine.

Without `--vault`, every command (and the `obsidian` MCP, `obsidian-index`, `obsidian-capture`) picks the vault in this order:

1. `$DANFAULT_VAULT`
2. the vault with a project whose `repos` lists the current repo's origin
3. the vault that contains the current directory
4. `default_vault`

In a linked repo (or inside `01-projects/<project>/`), `tasks` shows only that project; `--all` shows every project. When several projects list the same repo, the first one is used with a warning. `which` shows the result and the reason.

## Syncing

**Syncing:** Obsidian Sync skips `project.json` (not a note) and dot-files (`.indexignore`, `.gitkeep`). Back the vault up with git instead: see `docs/vault-git-backup.md` or run `/obsidian-vault:vault-git-setup`. If you rely only on Sync, turn on *Settings → Sync → Selective sync → Sync all other types* on every device.

## Enhanced projects

A project with a `project.json` is "enhanced". `health-check` lists projects that are not enhanced yet, as a guide for migrating old projects and keeping new ones up to date. This list does not change the exit code.

`project init` creates a project, or enhances an existing one: it adds only the missing folders, `SUMMARY.md` and `project.json` (status copied from `SUMMARY.md`). It never overwrites a file. The `/project-init` skill collects the metadata and calls it.

## Next ideas

- Keep per-project sources in `project.json`.
- When `project.json` has more fields, show the fields each project is missing in `health-check`.
- `/vault-session-review` uses these commands to propose new tasks, task and project status changes, and runs `health-check`.
