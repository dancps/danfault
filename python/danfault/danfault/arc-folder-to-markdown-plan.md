# Plan: Arc sidebar folder → Markdown list

## Goal
Build a small command-line tool that reads my **Arc browser** sidebar data and prints (or saves) a **Markdown list of the tabs inside a named folder**, including nested subfolders. Each tab becomes a `- [Title](URL)` line. Subfolders become nested list items.

This must work on folders even when their tabs are not currently open, so it reads Arc's saved sidebar data on disk rather than the live tab API. (Arc's sidebar folders are not standard Chrome tab groups or bookmarks, so a Chrome extension can't see them cleanly — that's why this is a local script.)

## Constraints / preferences
- **Python 3, standard library only.** No pip installs. Single self-contained script.
- Read-only with respect to Arc's data: never modify the original file. Work on a copy.
- Don't require Arc to be running.

## IMPORTANT: inspect the real data before writing the parser
Arc's on-disk format is undocumented and the exact field names vary by version, so **do not assume the schema from this plan**. Before writing parsing logic:

1. Locate the data file (see paths below).
2. Copy it to the working directory.
3. Load it and print: the top-level keys, the shape of `sidebar` / `containers`, and 3–5 sample entries from the flat item list (pretty-printed JSON, truncated).
4. From those samples, work out empirically how the format distinguishes: **spaces**, **folders**, and **tabs**, and where the tab **URL** and **title** live, and how parent/child relationships are encoded (e.g. `childrenIds` arrays and/or `parentID`).
5. Only then write the parser against the structure you actually observed. Show me the sample output so I can confirm before you finalize.

## Where the data lives
The file is `StorableSidebar.json`. Detect the OS and search these locations (expand `~` / env vars):

- **macOS:** `~/Library/Application Support/Arc/StorableSidebar.json`
- **Windows:** under `%LOCALAPPDATA%\Packages\TheBrowserCompany.Arc_*\LocalCache\Local\Arc\StorableSidebar.json` (glob the package folder)

If not found, print the paths you checked and let me pass an explicit `--file PATH`.

## How the format is (probably) shaped — verify against step "inspect"
Expect a flat list of items each with an `id`, a parent reference, and a `childrenIds` list. Items are one of:
- a **tab** (has a saved URL + saved title),
- a **folder / list** (has a title + children, no URL),
- a **space** (top-level grouping; has a name and links to pinned/unpinned containers).

Rebuild the tree by indexing every item by `id`, then walking `childrenIds`. Treat the same recursion for folders nested in folders.

## CLI interface
```
arc_md.py --list [--file PATH]
    List every folder found, grouped by space, with full path and tab count.
    Disambiguates folders that share a name across spaces.

arc_md.py "Folder Name" [--space "Space Name"] [--out output.md] [--headings] [--file PATH]
    Print the Markdown for that folder to stdout, or write to --out.
    --space narrows the match when a folder name is not unique.
    --headings renders each subfolder as a Markdown heading (###) instead of a nested bullet.
```

## Output format
Default (nested bullets):
```markdown
- [Anthropic](https://anthropic.com)
- [Docs](https://docs.claude.com)
- Subfolder name
  - [Nested tab](https://example.com)
```

With `--headings`, top-level folder name becomes an `##` heading, each subfolder a `###`, and tabs are flat bullets under their heading.

Escape Markdown-significant characters in titles (`[`, `]`, `|`, backticks). Keep any emoji in folder/tab titles as-is. Skip items with no resolvable URL but log how many were skipped.

## Edge cases to handle
- Folder name not found → print the closest matches and exit non-zero.
- Folder name not unique and no `--space` given → list the candidates with their spaces and ask me to disambiguate.
- Archived / suspended tabs that still have a saved URL → include them.
- Empty folder → emit a note, not a crash.
- Malformed or unexpected JSON → fail with a clear message, not a stack trace.

## Acceptance criteria
1. `--list` shows my real folders grouped by space with correct counts.
2. Running it on one real folder produces Markdown whose links open the right pages.
3. Nested subfolders are represented correctly in both default and `--headings` modes.
4. Original `StorableSidebar.json` is untouched.
5. Single file, runs with `python3 arc_md.py ...`, no external dependencies.

## Suggested build order
1. File location + `--file` override + copy-to-workdir.
2. Load + inspect/print samples (share with me to confirm schema).
3. Index items, rebuild tree, classify spaces/folders/tabs.
4. `--list` command.
5. Folder lookup (+ `--space` disambiguation) and recursive Markdown rendering.
6. `--out` and `--headings` options, escaping, edge cases.
7. Run against my real data and show output.
