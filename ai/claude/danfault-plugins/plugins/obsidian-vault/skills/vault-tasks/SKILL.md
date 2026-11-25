---
name: vault-tasks
description: Track projects and tasks in the Obsidian vault with the `danfault vault` CLI — list projects and their status, create or enhance a project, list a project's tasks, add a task note, change a project's or a task's status, and check metadata health. Use when the user asks what is pending or open, what projects exist, to add or close a task, to mark a project finished/active, or whether the vault's project metadata is in sync.
user-invocable: true
---

# Skill: Vault Projects and Tasks

Use the `danfault vault` CLI for every read and status change, so results match what the user gets in a terminal. Do not reimplement it by reading files, except to create a task note.

## Layout

Each project is a folder in `<vault>/01-projects/<project>/` (`<vault>` = `danfault vault path`):

| Path | Role |
|---|---|
| `SUMMARY.md` | Project overview. The CLI reads `title` and `status` from its frontmatter. |
| `project.json` | Optional metadata written by the CLI: `status` (wins over `SUMMARY.md`), `tasks` (`{"<task id>": "<status>"}`, wins over each task's frontmatter) and `repos` (`["owner/repo"]`, code repos linked to the project). A project with this file is "enhanced". |
| `tasks/<task>.md` | One note per task. The file name (without `.md`) is the task id. |

## Commands

All commands take `--vault NAME`. Without it, the vaults are `$DANFAULT_VAULT`, else every vault linked to the current repo (`repos` in `<vault>/vault.json` or in a project's `project.json`), else the vault that contains the current directory, else `default_vault`. Read commands cover every linked vault (with a `VAULT` column); write commands use the vault that has the project, or need `--vault`. Run `danfault vault which` to see the vault and project for the current directory.

| Command | Use |
|---|---|
| `danfault vault list projects [--status S]` | Projects with title, status and task count |
| `danfault vault which` | Vault and project for the current directory, and why |
| `danfault vault tasks [--project P] [--status S] [--all]` | Task notes, optionally for one project or one status. In a linked repo or a project folder, only that project's tasks (`--all` for every project) |
| `danfault vault project init P [--title T] [--domain D] [--goal G] [--status S]` | Create a project, or add what an existing one is missing (folders, `SUMMARY.md`, `project.json`). Never overwrites. Use `/obsidian-vault:project-init` to collect metadata for a new project. |
| `danfault vault project set-status P S` | Write `status: S` to `P/project.json` (creates it) |
| `danfault vault link V [--repo owner/repo]` / `unlink V` | Link a code repo to vault `V` (`repos` in `V/vault.json`). A repo can be linked to several vaults. Nothing is written to the repo |
| `danfault vault project link P [--repo owner/repo]` | Link a code repo to `P` (default: the current repo's origin). Nothing is written to the repo, so it is safe in shared repos |
| `danfault vault task set-status P T S` | Write task `T`'s status to `P/project.json` (for example `done`, `blocked`) |
| `danfault vault health-check [--project P]` | Status divergences, missing statuses, malformed metadata (exit 1); also lists projects without `project.json` (does not fail) |

Status is free text (for example `active`, `finished`, `open`, `done`). A missing status shows as `unknown`. Filters match the exact value.

## Rules

- Never edit `SUMMARY.md` or a task's frontmatter to change a status unless the user asks for it. Both `set-status` commands write only `project.json`.
- After a `set-status`, if the CLI warns that the note now disagrees, tell the user and point to `danfault vault health-check --project P`. Do not fix the note yourself.
- Warnings go to stderr. Report them to the user; do not drop them.
- When the user does not name the project, run `danfault vault which`. If it shows a project, use it. Otherwise run `danfault vault list projects` and ask which one, unless the current context makes it clear.
- If the session works in a code repo that is not linked to any project, offer `danfault vault project link <project>` once.
- If a subcommand is unknown, the installed CLI is out of date. Tell the user to run `uv tool install --force --reinstall <danfault-repo>/python/danfault`.

## Adding a task

1. Confirm the project exists with `danfault vault list projects`.
2. Write `<vault>/01-projects/<project>/tasks/<kebab-case-slug>.md`. Create `tasks/` if it is missing. Do not overwrite an existing file.

   ```markdown
   ---
   title: <title>
   type: task
   domain: <the project's domain, from SUMMARY.md>
   tags: [task]
   status: open
   created: <today, YYYY-MM-DD>
   ---

   # <title>

   ## Task

   <what to do and how to know it is done>
   ```

3. Show the result with `danfault vault tasks --project <project>`.
