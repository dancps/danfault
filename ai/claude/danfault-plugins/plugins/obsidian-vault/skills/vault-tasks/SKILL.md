---
name: vault-tasks
description: Track projects and tasks in the Obsidian vault with the `danfault vault` CLI — list projects and their status, list a project's tasks, add a task note, change a project's status, and check metadata health. Use when the user asks what is pending or open, what projects exist, to add or close a task, to mark a project finished/active, or whether the vault's project metadata is in sync.
user-invocable: true
---

# Skill: Vault Projects and Tasks

Use the `danfault vault` CLI for every read and status change, so results match what the user gets in a terminal. Do not reimplement it by reading files, except to create a task note.

## Layout

Each project is a folder in `<vault>/01-projects/<project>/` (`<vault>` = `danfault vault path`):

| Path | Role |
|---|---|
| `SUMMARY.md` | Project overview. The CLI reads `title` and `status` from its frontmatter. |
| `project.json` | Optional metadata written by the CLI. Its `status` wins over `SUMMARY.md`. A project with this file is "enhanced". |
| `tasks/<task>.md` | One note per task. The file name (without `.md`) is the task id. |

## Commands

All commands take `--vault NAME` (default: `default_vault`).

| Command | Use |
|---|---|
| `danfault vault list projects [--status S]` | Projects with title, status and task count |
| `danfault vault tasks [--project P] [--status S]` | Task notes, optionally for one project or one status |
| `danfault vault project set-status P S` | Write `status: S` to `P/project.json` (creates it) |
| `danfault vault health-check [--project P]` | Status divergences, missing statuses, malformed metadata (exit 1); also lists projects without `project.json` (does not fail) |

Status is free text (for example `active`, `finished`, `open`, `done`). A missing status shows as `unknown`. Filters match the exact value.

## Rules

- Never edit `SUMMARY.md` or a task's frontmatter to change a status unless the user asks for it. `set-status` writes only `project.json`.
- After `set-status`, if the CLI warns that `SUMMARY.md` now disagrees, tell the user and point to `danfault vault health-check --project P`. Do not fix the note yourself.
- Warnings go to stderr. Report them to the user; do not drop them.
- When the user does not name the project, run `danfault vault list projects` and ask which one, unless the current context makes it clear.
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
