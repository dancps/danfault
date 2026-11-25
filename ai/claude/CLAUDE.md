# Global guidelines

Personal defaults applied to every Claude Code session on this machine. Project-level `CLAUDE.md` files take precedence over anything here.

## Code

- Don't add features, refactor, or introduce abstractions beyond what was asked. A bug fix doesn't need surrounding cleanup; a one-off script doesn't need a helper module. No speculative generality.
- Default to no comments. Only add one when the *why* isn't obvious from the code itself (a workaround, a non-obvious constraint) — never to restate what the code already says.
- Don't add error handling or validation for cases that can't happen. Trust internal code; validate only at real boundaries (user input, external APIs, network calls).
- Prefer editing an existing file over creating a new one. Prefer deleting dead code outright over commenting it out or leaving compatibility shims.
- Don't hard-wrap prose in text files (Markdown, plain text, docs) to a fixed width. Write each paragraph or list item as one line and let the editor soft-wrap it — unless the project explicitly sets a line width.

## Git

- Claude may run `git commit` itself. Commit finished work on a feature branch; ask before committing directly on the default branch.
- Create new commits instead of amending, unless told otherwise.
- Never force-push, reset --hard, or skip hooks without being asked directly.
- Commit messages are always a single line, focused on *why*, not a restatement of the diff. No body, ever.
- Never add Claude attribution to commits or PRs — no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" line. This overrides any default attribution guidance.

## Communication

- Be concise. Skip preamble and trailing summaries unless asked for one.
- State results and decisions directly instead of narrating the process.
- For open-ended questions ("what do you think?", "how should I approach this?"), give a short recommendation with the main trade-off — not an exhaustive survey — and wait before implementing.
- Ask before destructive or hard-to-reverse actions (deleting files/branches, force operations, modifying shared/remote state). Everything local and reversible can proceed without asking.
