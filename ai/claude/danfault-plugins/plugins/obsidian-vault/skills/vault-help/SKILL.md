---
name: vault-help
description: Display all available commands and tools for interacting with the Obsidian vault.
user-invocable: true
---

# Skill: Vault Help

Show all available vault commands.

## Usage
```
/obsidian-vault:vault-help
```

## Instructions

Display the following reference exactly as formatted:

---

## Vault Commands

### Configuration

Locations and domains are read from a machine-local config (never committed):
`~/.config/danfault/vault.yaml`. Resolve values with the `danfault vault` CLI:

| Command | Returns |
|---|---|
| `danfault vault path [--vault NAME]` | Absolute path to a vault (default: `default_vault`) |
| `danfault vault domains [--vault NAME]` | The vault's declared note domains, one per line |
| `danfault vault repos [--github]` | Every configured repo's path (or `owner/repo` slug) |
| `danfault vault repo NAME [--github]` | One repo's path (or its `owner/repo` slug) |
| `danfault vault init NAME --path DIR [--domain D]... [--default]` | Create a vault with the standard layout and register it in the config |

### Projects and Tasks

Read from `01-projects/<project>/` (`SUMMARY.md`, optional `project.json`, `tasks/<task>.md`). Every command takes `--vault NAME`.

| Command | Returns |
|---|---|
| `danfault vault list projects [--status S]` | Projects with title, status and task count |
| `danfault vault tasks [--project P] [--status S]` | Task notes from `tasks/` |
| `danfault vault project init P [--title T] [--domain D] [--goal G] [--status S]` | Creates a project, or adds what an existing one is missing; never overwrites |
| `danfault vault project set-status P S` | Writes the status to `P/project.json`; `SUMMARY.md` is not touched |
| `danfault vault task set-status P T S` | Writes task `T`'s status to `P/project.json`; the task note is not touched |
| `danfault vault health-check [--project P]` | Status divergences, missing statuses, malformed metadata; lists projects without `project.json` |

Skills use these instead of hardcoding paths, so the same skill works on any
machine and across separate work/personal vaults.

### Skills

| Command | When to use |
|---|---|
| `/obsidian-vault:capture` | Save a quick insight or note to `00-inbox/` with frontmatter |
| `/obsidian-vault:captains-log` | Pull today's work-repo git activity → write a journal entry to `06-daily/` |
| `/obsidian-vault:obsidian-index` | Manually reindex the vault (use after editing notes outside Claude) |
| `/obsidian-vault:obsidian-index --full` | Full reindex — clears and rebuilds the entire index |
| `/obsidian-vault:vault-session-review` | Review session: suggest captures, report, and **update `status.md`** |
| `/obsidian-vault:vault-report` | Write a dated session report to a project's `reports/` folder |
| `/obsidian-vault:project-init` | Scaffold a new project (or enhance an existing one) via `danfault vault project init` |
| `/obsidian-vault:vault-tasks` | List projects/tasks, add a task, change a project's status, check metadata health (Claude also uses it on its own) |
| `/obsidian-vault:vault-help` | Show this reference |

### MCP Tools (available in any Claude session)

One `obsidian` MCP server serves every vault in `~/.config/danfault/vault.yaml`. Each tool below (except `obsidian_list_vaults`) takes an optional `vault` name; without it, `default_vault` is used.

| Tool | What it does |
|---|---|
| `obsidian_list_vaults` | List the registered vaults, the default, and which are not indexed yet |
| `obsidian_search` | Hybrid BM25 + semantic search across the vault |
| `obsidian_read_note` | Read a full note by vault-relative path |
| `obsidian_list_notes` | List notes filtered by folder or tag |
| `obsidian_get_context` | Get a compact context block for a topic (for prompt injection) |

### Automatic Behaviors (hooks)

| Trigger | What happens |
|---|---|
| Claude writes/edits a `.md` note in any registered vault | That vault is reindexed in the background (`danfault:vault-reindex` hook, installed by `ai/claude/install.sh`) |

### Vault Structure

```
vault/
├── 00-inbox/       New notes land here (via /obsidian-vault:capture or manual triage)
├── 01-projects/    Active and past projects (SUMMARY + status + learnings + reports)
├── 02-areas/       Ongoing responsibilities (policies, troubleshooting, tool ideas)
├── 03-resources/   Reference material (tools, frameworks, setup notes)
├── 04-archive/     Completed projects, old meetings, feedback
├── 06-daily/       Daily notes (2025+, date-named)
├── 07-templates/   Note templates (excluded from index)
└── .indexignore    Exclusion rules for AI indexing
```

### What's excluded from the index

- `07-templates/` — placeholder variables degrade retrieval
- `08-attachments/` — binary files
- `06-daily/` — low-signal logs (remove from .indexignore if daily notes become substantive)
- `04-archive/feedbacks/` — sensitive peer review content
- `01-projects/**/reports/` — operational snapshots (S3 paths, execution IDs, commits)

### Project structure (inside `01-projects/<name>/`)

| File/Folder | Purpose | Indexed? |
|---|---|---|
| `SUMMARY.md` | Stable overview, goal, key links | ✅ |
| `project.json` | CLI metadata (`status`, `tasks` statuses); wins over the notes | ❌ |
| `tasks/` | One note per task | ✅ |
| `status.md` | Live status — overwrite each session | ✅ |
| `learnings/` | Durable platform knowledge | ✅ |
| `documents/` | Reference docs, PRDs | ✅ |
| `reports/` | Operational session snapshots | ❌ |
