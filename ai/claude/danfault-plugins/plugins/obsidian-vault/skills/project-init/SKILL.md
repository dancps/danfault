---
name: project-init
description: Initialize a new project in the Obsidian vault's 01-projects/ folder (SUMMARY.md, project.json, tasks/, learnings/, documents/, reports/) through `danfault vault project init`, or add what an existing project is missing.
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

The folders and files come from `danfault vault project init`. Do not create them with the Write tool. The command never overwrites a file, so it is also safe on an existing project: it only adds what is missing (for example `tasks/` or `project.json`).

1. **Get the project name** — if passed as argument, use it. Otherwise ask:
   "What's the project name? (will become the folder name, e.g. `my-project`)"

2. **Check if it exists** — run `danfault vault list projects`. If the project is listed, skip step 3: its `SUMMARY.md` is kept, so do not ask for metadata. Run `danfault vault project init <project-name>` and go to step 4.

3. **Get metadata** for a new project — ask for:
   - `title` — human-readable title (e.g. "My Project")
   - `domain` — one of the vault's declared domains. List them with `danfault vault domains`; if none fit, ask the user.
   - `goal` — one sentence: what is this project trying to achieve?
   - `status` — `active` or `draft`

   Then run:
   ```bash
   danfault vault project init <project-name> --title "<title>" --domain <domain> --goal "<goal>" --status <status>
   ```

4. **Report** — show the user the `created` / `kept existing` lines and any warning the command prints.

5. **Trigger reindex:**
   ```bash
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index
   ```

6. **Confirm** — tell the user the path and suggest: "Add tasks as notes in `tasks/`. Use `danfault vault tasks --project <project-name>` to list them, `danfault vault health-check` to find out-of-sync metadata, and `/vault-review` at the end of each session to capture learnings here."
