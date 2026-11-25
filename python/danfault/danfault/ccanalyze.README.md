# ccanalyze

Analyze a Claude Code conversation to see **what made its context long**.

Give it a session id (full or a prefix/substring). The script locates the
transcript under `~/.claude/projects/*/<id>.jsonl` — it scans every project
dir, so it's agnostic to which repo/org the session belonged to.

## Usage

```bash
ccanalyze <session-id-or-prefix>       # full report
ccanalyze <id> --top 25                # show more of the biggest tool results
ccanalyze <id> --json                  # machine-readable output
ccanalyze --list                       # recent sessions across all projects
ccanalyze --resolve <any-id>           # map a resume id / uuid to its session file
ccanalyze <id> --projects-dir /path    # override (or set CLAUDE_PROJECTS_DIR)
```

## Resume id vs. conversation id

A session is stored in one file named by its `sessionId` — that id **is** the
conversation id, and `--resume` lists sessions by it. The confusion comes from
resume *pointers*:

- `leafUuid` records (`last-prompt` / `mode` / `aiTitle` events) mark the tip
  of the conversation at each prompt — the resumable checkpoints. A leafUuid is
  the `uuid` of the last message at that point, **not** the session id.
- When a resume *forks* a session, a new file with a new `sessionId` is created;
  its first message's `parentUuid` points to a `uuid` in the original file.

So to map any id back to a conversation, search across files for a matching
`sessionId`, `uuid`, `leafUuid`, or `parentUuid` — which is what `--resolve`
does, reporting how it matched.

## What it reports

- **Real context-window usage** — peak tokens actually sent to the model,
  read from `message.usage` (`input + cache_read + cache_creation`). This is
  the number that matters, not the file size.
- **File bloat** — `toolUseResult` bytes, the raw tool output stored on disk
  but *not* re-sent to the model. Inflates the `.jsonl` file, not the context.
- **Events by type** and disk bytes each.
- **Cumulative tool-result bytes by tool** — which tool (Bash, Read, …) filled
  the context.
- **Biggest single tool results** — the individual calls that hurt most,
  joined back to their tool name via `tool_use_id`.
- A one-line verdict naming the biggest driver.

## How it works

Claude Code stores each conversation as newline-delimited JSON at
`~/.claude/projects/<slugified-cwd>/<session-id>.jsonl`, one event per line.
Key fields:

- `message.usage` (assistant events) → real token cost.
- `message.content[].tool_result` joined to `tool_use.name` via
  `tool_use_id` → which tool produced each result sent to the model.
- top-level `toolUseResult` → stored-only raw copy (file bloat, ignore for
  context reasoning).

Pure Python stdlib, no dependencies.
