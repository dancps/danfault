---
name: capture
description: Capture an insight or note into the Obsidian vault's 00-inbox/ with proper frontmatter, then trigger an incremental reindex so it's immediately searchable.
user-invocable: true
---

# Skill: Capture Note to Vault

Use when the user wants to save an insight, reference, or note from the current session into the Obsidian vault.

## Usage
```
/capture
/capture "Some insight about X"
```

## Instructions

1. **Get the content** — if the user passed text after `/capture`, use that. Otherwise ask: "What would you like to capture?"

   If the content is vague or the user says "from the session" or "from recent work", you may read existing reports in the relevant project's `reports/` folder to gather context:
   ```bash
   ls "$(danfault vault path)"/01-projects/<project>/reports/ 2>/dev/null
   ```
   Read the relevant report files to extract the insight. **Never modify, overwrite, or delete any report file — reports are read-only sources for capture.**

2. **Get metadata** — ask for (or infer from context):
   - `title` — short descriptive title that becomes the filename slug. File will be saved as `YYYY-MM-DD-<slug>.md`. **Good titles are specific and scannable:** `pit-join-vs-exact-join`, `strict-less-than-semantics`, `stddev-nan-on-single-value-window`. Avoid vague titles like `session-notes`, `insight`, `fix`.
   - `domain` — the note's domain. List the vault's declared domains with `danfault vault domains` and pick the best match; if none fit, ask the user. Each vault declares its own set (in `~/.config/danfault/vault.yaml`), so a work vault and a personal vault can offer different domains.
   - `tags` — 1–3 relevant tags (infer if obvious)

3. **Run the capture tool:**
   ```bash
   VAULT_PATH="$(danfault vault path)" \
   DB_PATH=~/danfault/python/obsidian-mcp/data/vectors.db \
   uv run --project ~/danfault/python/obsidian-mcp \
     obsidian-capture "<content>" \
     --title "<title>" \
     --domain "<domain>" \
     --tags <tag1> <tag2>
   ```

4. **Confirm** — tell the user the note path and that it's now searchable via `obsidian_search`.
