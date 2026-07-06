---
name: vault-help
description: Display all available commands and tools for interacting with the Obsidian vault.
user-invocable: true
---

# Skill: Vault Help

Show all available vault commands.

## Usage
```
/vault-help
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

Skills use these instead of hardcoding paths, so the same skill works on any
machine and across separate work/personal vaults.

### Skills

| Command | When to use |
|---|---|
| `/capture` | Save a quick insight or note to `00-inbox/` with frontmatter |
| `/captains-log` | Pull today's work-repo git activity → write a journal entry to `06-daily/` |
| `/obsidian-index` | Manually reindex the vault (use after editing notes outside Claude) |
| `/obsidian-index --full` | Full reindex — clears and rebuilds the entire index |
| `/vault-session-review` | Review session: suggest captures, report, and **update `status.md`** |
| `/vault-report` | Write a dated session report to a project's `reports/` folder |
| `/project-init` | Scaffold a new project in `01-projects/` with SUMMARY.md + folders |
| `/vault-help` | Show this reference |

### MCP Tools (available in any Claude session)

| Tool | What it does |
|---|---|
| `obsidian_search` | Hybrid BM25 + semantic search across the vault |
| `obsidian_read_note` | Read a full note by vault-relative path |
| `obsidian_list_notes` | List notes filtered by folder or tag |
| `obsidian_get_context` | Get a compact context block for a topic (for prompt injection) |

### Automatic Behaviors (hooks)

| Trigger | What happens |
|---|---|
| Claude writes/edits a file in `<vault>/` | Vault is automatically reindexed in the background |

### Vault Structure

```
vault/
├── 00-inbox/       New notes land here (via /capture or manual triage)
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
| `status.md` | Live status — overwrite each session | ✅ |
| `learnings/` | Durable platform knowledge | ✅ |
| `documents/` | Reference docs, PRDs | ✅ |
| `reports/` | Operational session snapshots | ❌ |
