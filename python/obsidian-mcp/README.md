# obsidian-mcp

MCP server for hybrid (BM25 + semantic) retrieval over Obsidian vaults, plus the indexer and capture CLIs it depends on. One server serves every vault registered on the machine.

## Vaults

Vaults come from the machine-local danfault config, the same file `danfault vault` reads (never committed):

```yaml
# ~/.config/danfault/vault.yaml
default_vault: mestrado
vaults:
  mestrado:
    path: ~/Documents/Obsidian/mestrado
    domains: [research, thesis, admin]
    # db: ~/somewhere/mestrado.db   # optional; default: data/<name>.db in this project
```

`danfault vault init NAME --path DIR` creates a vault and adds it here.

## Setup

1. Index each vault:
   ```bash
   uv run --project ~/danfault/python/obsidian-mcp obsidian-index --vault mestrado --full
   ```
2. Register the server once per machine:
   ```bash
   claude mcp add obsidian --scope user -- uv run --project ~/danfault/python/obsidian-mcp obsidian-mcp
   ```

A new vault then only needs an entry in `vault.yaml` and an index run. The server re-reads the config on each call, so no restart or new registration is needed.

## Tools

Every tool except `obsidian_list_vaults` takes an optional `vault` name; without it, `default_vault` is used.

| Tool | What it does |
|---|---|
| `obsidian_list_vaults` | Registered vaults, the default, and which are not indexed yet |
| `obsidian_search` | Hybrid BM25 + semantic search |
| `obsidian_read_note` | Full note content by vault-relative path |
| `obsidian_list_notes` | Notes filtered by folder or tag |
| `obsidian_get_context` | Compact context block for a topic |

## CLIs

```bash
obsidian-index [--vault NAME] [--full]                 # incremental by default
obsidian-capture "text" [--vault NAME] [--title T] [--domain D] [--tags a b]
```

Run them with `uv run --project ~/danfault/python/obsidian-mcp <cli>`. `obsidian-capture` writes to `00-inbox/` and reindexes the vault.
