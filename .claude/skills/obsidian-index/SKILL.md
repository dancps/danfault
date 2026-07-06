---
name: obsidian-index
description: Run an incremental reindex of the Obsidian vault so new or changed notes become searchable via obsidian_search.
user-invocable: true
---

# Skill: Reindex Obsidian Vault

Use when notes have been added or edited and you want them immediately available to `obsidian_search`.

## Usage
```
/obsidian-index
/obsidian-index --full
```

## Instructions

1. **Check for `--full` flag** — if present, do a full reindex (clears and rebuilds). Otherwise do incremental (only changed files).

2. **Run the indexer:**

   Incremental:
   ```bash
   VAULT_PATH="$(danfault vault path)" \
   DB_PATH=~/danfault/python/obsidian-mcp/data/vectors.db \
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index
   ```

   Full:
   ```bash
   VAULT_PATH="$(danfault vault path)" \
   DB_PATH=~/danfault/python/obsidian-mcp/data/vectors.db \
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index --full
   ```

3. **Report** — show the output (chunks indexed, files unchanged).
