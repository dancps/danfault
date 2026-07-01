---
name: vault-session-review
description: Review the current session and suggest what's worth capturing to the Obsidian vault. Covers learnings, decisions, debugging patterns, platform insights, operational output, and project status updates.
user-invocable: true
---

# Skill: Vault Review

Use at the end of a session to identify content worth preserving in the vault.

## Usage
```
/vault-session-review
```

## Instructions

1. **Review the session** across three dimensions:

   **A — Durable knowledge** (goes to `learnings/`, `03-resources/`, or `00-inbox/` via `/capture`):
   - Learnings: how something works, a platform behavior, a framework detail
   - Decisions: architectural or design choices made with rationale
   - Debugging patterns: root causes found, investigation steps that worked
   - Reference material: commands, configs, or workflows that would be useful again

   **B — Operational output** (goes to `reports/` via `/vault-report`):
   - Commits made and what they fixed
   - Execution IDs, run IDs, adhoc job IDs
   - Output locations (S3 paths, notebook paths, table names)
   - Validation or test results
   - Branches touched across repos
   - Significant files created or modified

   **C — Project status** (overwrites `01-projects/<name>/status.md`):
   - What was completed this session (per-op validation results, fixes applied)
   - What is blocked and why
   - What comes next (concrete next steps for the next session)
   - Active clusters, branches, PR numbers

2. **Filter ruthlessly for durable knowledge** — skip:
   - Anything too session-specific to generalize
   - Content already well-documented in the codebase or vault
   - Ephemeral output that belongs in a report, not a learning

3. **Present three sections** — only show a section if there's content for it:

   ```
   Worth capturing (durable):
   1. [Learning] "date.cast('long') gives days, not epoch seconds" → 03-resources/
   2. [Decision] "feature X uses PIT join, not exact join" → 01-projects/.../learnings/

   Worth reporting (operational):
   - Commits: abc1234 (null fix), def5678 (NaN guard)
   - Adhoc: execution <run-id>, S3 paths for the outputs
   - Branches: you/feature-branch (<work-repo>)
   → Suggest: /vault-report my-project

   Project status update (01-projects/my-project/status.md):
   - Feature A: ✅ DONE (PR #12345)
   - Feature B: ⏳ divergence unresolved
   - Next: investigate the discrepancy in the upstream source
   ```

   If the session touches a project tracked in `01-projects/`, **always** include the status section — even if no durable knowledge or operational output was produced.

4. **Handle each section:**

   For **durable captures** — ask "Want to capture this?" for each item and run `/capture`:
   ```bash
   VAULT_PATH="$(danfault vault path)" \
   DB_PATH=~/danfault/python/obsidian-mcp/data/vectors.db \
   uv run --project ~/danfault/python/obsidian-mcp \
     obsidian-capture "<content>" --title "<title>" --domain "<domain>" --tags <tags>
   ```
   Or write directly to the appropriate project folder if it already exists in the vault.

   For **operational output** — ask "Want to write a session report?" and if yes, invoke `/vault-report` with the project name pre-filled.

   For **project status** — ask "Want to update status.md?" and if yes, **overwrite** (do not append) `01-projects/<project>/status.md` with the new state. The file must always reflect current reality, not accumulated history. Keep the same structure as the existing file: per-op validation table, detail sections for blocked items, recent commits, next session steps, and persistent operational notes (clusters, permissions). Update the `Last updated:` line to today's date.
