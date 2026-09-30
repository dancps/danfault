---
name: obsidian-index
description: Run an incremental reindex of the Obsidian vault so new or changed notes become searchable via obsidian_search.
user-invocable: true
---

# Skill: Reindex Obsidian Vault

Use when notes have been added or edited and you want them immediately available to `obsidian_search`.

## Usage
```
/obsidian-vault:obsidian-index
/obsidian-vault:obsidian-index --full
/obsidian-vault:obsidian-index --vault NAME
```

## Instructions

1. **Check for `--full` flag** — if present, do a full reindex (clears and rebuilds). Otherwise do incremental (only changed files). If `--vault NAME` is given, append it to the command below; without it, the indexer uses `default_vault` from `~/.config/danfault/vault.yaml`.

2. **Run the indexer:**

   Incremental:
   ```bash
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index
   ```

   Full:
   ```bash
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index --full
   ```

3. **Report** — show the output (chunks indexed, files unchanged).
