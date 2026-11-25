# Vault projects and tasks

`danfault vault` reads project-management data from an Obsidian vault without changing how the vault is organized.

## Commands

```
danfault vault list projects [--status S]
danfault vault tasks [--project P] [--status S]
danfault vault project set-status P S
danfault vault health-check [--project P]
```

## Decision: infer from the folder layout, store CLI metadata in JSON

- A project is a folder in `01-projects/`. A task is a note in `01-projects/<project>/tasks/`.
- `SUMMARY.md` and task notes are read-only for the CLI. No migration is needed: notes without a status show `unknown`.
- Metadata the CLI writes goes to an optional `01-projects/<project>/project.json`. When `project.json` has a field, it wins over the `SUMMARY.md` frontmatter.
- Status is free text. There is no fixed vocabulary.
- When `project.json` and `SUMMARY.md` disagree, the commands print a warning to stderr. `set-status` reminds you to update the note. `health-check` lists every divergence and exits 1.

## Enhanced projects

A project with a `project.json` is "enhanced". `health-check` lists projects that are not enhanced yet, as a guide for migrating old projects and keeping new ones up to date. This list does not change the exit code.

## Next ideas

- Keep per-project repos and sources in `project.json` (or in separate `repos.json` / `sources.json`; not decided).
- When `project.json` has more fields, show the fields each project is missing in `health-check`.
- Add `set-status` for tasks.
