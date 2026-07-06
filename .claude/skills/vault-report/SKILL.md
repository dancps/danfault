---
name: vault-report
description: Write a dated session report to a project's reports/ folder in the Obsidian vault. Confirms the project and summarizes content before writing.
user-invocable: true
---

# Skill: Vault Report

Write a session report to `01-projects/<name>/reports/` in the vault.

> `<vault>` resolves via `danfault vault path`; `<work-repo>` in the examples is any repo from `danfault vault repos` (all from `~/.config/danfault/vault.yaml`).

## Usage
```
/vault-report
/vault-report my-project
```

## Instructions

1. **Identify the project** — if a project name was passed as argument, use it. Otherwise list available projects and ask:
   ```bash
   ls "$(danfault vault path)"/01-projects/
   ```
   Ask: "Which project is this report for?"

2. **Confirm the project exists:**
   ```bash
   ls "$(danfault vault path)"/01-projects/<project-name>/reports/ 2>/dev/null || echo "not found"
   ```
   If not found, ask the user to confirm the exact project name.

3. **Gather report content** — scan the current session for operational output worth recording.

   **Always collect:**

   - **Working directories** — every directory that was the focus of work during the session (not just tool calls, but where the work actually happened). Examples: `<work-repo>`, `<vault>`, `~/danfault`. List each one.

   - **Branches touched** — for each working directory that is a git repo, check the active branch and recent commits:
     ```bash
     git -C <dir> branch --show-current 2>/dev/null
     git -C <dir> log --oneline --since="12 hours ago" --author="$(git config user.email)" 2>/dev/null
     ```

   - **Files touched** — significant files read, created, or edited during the session (grouped by directory if multiple repos were involved).

   **Include if present:**
   - Commits and what they changed
   - Execution IDs, run IDs, job IDs (adhoc, Databricks, CI, batch jobs)
   - Output locations (S3 paths, notebook paths, table names, file paths)
   - Results or outcomes (validation, test results, metrics, build output, errors)
   - Decisions too specific or volatile to go in `learnings/`
   - Open issues or blockers discovered

   Skip any category with no content for this session.

4. **Determine a short topic slug** from the session's main activity (e.g. `null-fix`, `initial-setup`, `ci-debug`, `smoke-tests`).

5. **Check for existing reports today:**
   ```bash
   ls "$(danfault vault path)"/01-projects/<project-name>/reports/$(date +%Y-%m-%d)*.md 2>/dev/null
   ```
   If one or more files already exist for today, show them to the user:
   ```
   Reports already exist for today:
     - 2026-05-18-smoke-tests.md
   ```
   Then continue normally — the slug will naturally differentiate the new file. If the proposed slug would produce a filename that already exists, append `-2`, `-3`, etc. until the name is unique. Never overwrite an existing report.

6. **Present a summary for confirmation** before writing anything:
   ```
   Project:  <project-name>
   File:     01-projects/<project-name>/reports/<YYYY-MM-DD>-<slug>.md

   Will include:
   - Working dirs: <work-repo>, <vault>
   - Branches: you/feature-branch (<work-repo>)
   - Files touched: SomeModule.scala, status.md (vault)
   - Commits: abc1234, def5678
   - Results: re-run pending, NaN guard confirmed

   Proceed?
   ```

   Wait for the user to confirm (or adjust) before writing.

7. **Write the report** with a structure that fits the content. Use H2 sections. Only include sections with content:

   ```markdown
   # Session Report — <YYYY-MM-DD> — <topic>

   ## Working directories

   - `<work-repo>` — branch: `you/feature-branch`
   - `<vault>` — vault updates

   ## Files touched

   - `path/to/file` — <what changed>

   ## Commits

   | Commit | Description |
   |---|---|
   | `<hash>` | <what it fixed> |

   ## <Other categories as needed>

   ## Notes
   <open questions, blockers, next steps>
   ```

   The structure is flexible — match it to what actually happened.

8. **Confirm** after writing — show the file path. Do NOT trigger a reindex (reports are excluded from the index by design).
