---
name: project-init
description: Initialize a new project in the Obsidian vault's 01-projects/ folder with a standard structure (SUMMARY.md, project.json, tasks/, learnings/, documents/, reports/).
user-invocable: true
---

# Skill: Initialize Project in Vault

Use when starting a new project that warrants tracking in the vault.

> `<vault>` below resolves via `danfault vault path` (from `~/.config/danfault/vault.yaml`).

## Usage
```
/obsidian-vault:project-init
/obsidian-vault:project-init "my-project"
```

## Instructions

1. **Get the project name** — if passed as argument, use it. Otherwise ask:
   "What's the project name? (will become the folder name, e.g. `my-project`)"

2. **Get metadata** — ask for:
   - `title` — human-readable title (e.g. "My Project")
   - `domain` — one of the vault's declared domains. List them with `danfault vault domains`; if none fit, ask the user.
   - `goal` — one sentence: what is this project trying to achieve?
   - `status` — `active` or `draft`

3. **Create the folder structure** using the Write tool:

   ```
   <vault>/01-projects/<project-name>/
     SUMMARY.md
     tasks/          (empty, create a .gitkeep)
     learnings/      (empty, create a .gitkeep)
     documents/      (empty, create a .gitkeep)
     reports/        (empty, create a .gitkeep)
   ```

4. **Write `SUMMARY.md`** with this template:

   ```markdown
   ---
   title: <title>
   type: project
   domain: <domain>
   tags: []
   status: <status>
   created: <today>
   ---

   # <title>

   **Goal:** <goal>

   ## Current Status

   > Update this section each session.

   ## Folder Structure

   | Folder | Purpose |
   |--------|---------|
   | `tasks/` | One note per task. List them with `danfault vault tasks --project <project-name>` |
   | `learnings/` | Reusable platform knowledge discovered during this project |
   | `documents/` | Reference docs, PRDs, external material |
   | `reports/` | Session outputs, validation results, analysis |

   ## Key Links

   _(add links to PRs, Databricks notebooks, Confluence pages here)_

   ## Notes for Next Session

   _(update before closing each session)_
   ```

5. **Create `project.json`** so the project is "enhanced" from the start (see the vault README, section "Projects and Tasks"):
   ```bash
   danfault vault project set-status <project-name> <status>
   ```

6. **Trigger reindex:**
   ```bash
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index
   ```

7. **Confirm** — tell the user the path and suggest: "Add tasks as notes in `tasks/` (frontmatter `title`, `type: task`, `status`, `created`). Use `danfault vault tasks --project <project-name>` to list them, `danfault vault health-check` to find out-of-sync metadata, and `/vault-review` at the end of each session to capture learnings here."
