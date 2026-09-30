# Global guidelines

Personal defaults applied to every Claude Code session on this machine.
Project-level `CLAUDE.md` files take precedence over anything here.

## Code

- Don't add features, refactor, or introduce abstractions beyond what was asked.
  A bug fix doesn't need surrounding cleanup; a one-off script doesn't need a
  helper module. No speculative generality.
- Default to no comments. Only add one when the *why* isn't obvious from the
  code itself (a workaround, a non-obvious constraint) — never to restate
  what the code already says.
- Don't add error handling or validation for cases that can't happen. Trust
  internal code; validate only at real boundaries (user input, external APIs,
  network calls).
- Prefer editing an existing file over creating a new one. Prefer deleting
  dead code outright over commenting it out or leaving compatibility shims.

## Git

- Only commit when explicitly asked.
- Create new commits instead of amending, unless told otherwise.
- Never force-push, reset --hard, or skip hooks without being asked directly.
- Keep commit messages short and focused on *why*, not a restatement of the diff.
  Use a single-line message; add a body only when the *why* can't fit in one line.
- Never add Claude attribution to commits or PRs — no `Co-Authored-By: Claude`
  trailer, no "Generated with Claude Code" line. This overrides any default
  attribution guidance.
- Show the drafted commit message for review before committing. Skip the
  review only for small work (a few files or a few changed lines).
- Never run `git commit` directly. Draft the message, write it to a file
  (`.git/claude-commit-message.txt`, or a scratch file if outside a repo),
  and hand back the exact `git commit -F <path>` command for the user to run
  themselves. See the `commit` skill for the full flow. A `PreToolUse` hook
  enforces this machine-wide — it isn't a bypassable suggestion.

## Communication

- Be concise. Skip preamble and trailing summaries unless asked for one.
- State results and decisions directly instead of narrating the process.
- For open-ended questions ("what do you think?", "how should I approach
  this?"), give a short recommendation with the main trade-off — not an
  exhaustive survey — and wait before implementing.
- Ask before destructive or hard-to-reverse actions (deleting files/branches,
  force operations, modifying shared/remote state). Everything local and
  reversible can proceed without asking.
