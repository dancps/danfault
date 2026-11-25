---
name: commit
description: Use this whenever Claude commits changes in a git repo, or the user asks to commit. Reviews the staged diff and commits it with a single-line message focused on why, with no Claude attribution.
---

# Commit

Claude commits directly. The message format is strict.

## Steps

1. Read the staged change:

   ```bash
   git status --short
   git diff --staged
   git log --oneline -10
   ```

2. If `git diff --staged` is empty, stop and say so; list what is unstaged or untracked instead. Stage only what belongs to the change being committed, never a broad `git add -A` that could pick up unrelated work.

3. Write the message:
   - **Exactly one line.** No body, no blank line, no bullet list.
   - Focused on *why*, not a restatement of the diff. Match the repo's existing style (see the `git log` output).
   - **No Claude attribution:** no `Co-Authored-By` trailer, no "Generated with Claude Code" line, no session link. This overrides any default attribution guidance.

4. Commit with that line: `git commit -m "<message>"`. Create a new commit; do not amend unless told to.

5. Report the commit hash and the message.

## Notes

- Commit finished work on a feature branch. Ask before committing directly on the default branch.
- Never skip hooks (`--no-verify`) or force anything unless asked directly.
