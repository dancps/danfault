---
name: captains-log
description: Aggregate today's git activity from your work repo and write a structured journal entry to the Obsidian vault's 06-daily/ folder.
user-invocable: true
---

# Skill: Captain's Log

Pulls recent git commits from your configured repos and writes a structured daily journal entry to the vault. Creates a searchable record of what shipped and why.

> Locations come from `~/.config/danfault/vault.yaml`: `<vault>` = `danfault vault path`, repos = `danfault vault repos` (add `--github` for slugs).

## Usage
```
/captains-log
```

## Instructions

1. **Get today's date:**
   ```bash
   date +%Y-%m-%d
   ```

2. **Pull recent git activity from your configured repos** — iterate over every repo in `~/.config/danfault/vault.yaml`:
   ```bash
   for repo in $(danfault vault repos); do
     echo "## $repo"
     git -C "$repo" log --oneline --since="24 hours ago" --author="$(git config user.email)" 2>/dev/null
   done
   ```
   Also check for any open PRs across those repos:
   ```bash
   for slug in $(danfault vault repos --github); do
     gh pr list --repo "$slug" --author "@me" --state open --json number,title,url 2>/dev/null
   done
   ```

3. **Check today's daily note** — see if one already exists at `<vault>/06-daily/<date>.md`. If it does, append to it; if not, create it.

4. **Write the journal entry** using the Write or Edit tool at `<vault>/06-daily/<date>.md`:

   ```markdown
   ---
   title: <date>
   type: daily
   domain: work
   tags: ["daily", "captains-log"]
   status: active
   ---

   ## Captain's Log — <date>

   ### Shipped
   <list of commits, one per line with description>

   ### Open PRs
   <list of open PRs with links>

   ### Notes
   <ask the user if they want to add any notes or reflections>
   ```

5. **Ask** if the user wants to add notes or reflections before saving.

6. **Reindex** — run incremental reindex so the entry is immediately searchable:
   ```bash
   VAULT_PATH="$(danfault vault path)" \
   DB_PATH=~/danfault/python/obsidian-mcp/data/vectors.db \
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index
   ```

7. **Confirm** — tell the user the note path.
