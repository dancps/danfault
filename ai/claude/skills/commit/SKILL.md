---
name: commit
description: Use this whenever Claude wants to commit changes in a git repo, or the user asks to draft/prepare a commit. Reviews the currently staged diff, drafts a commit message into a local review file, and prints the exact `git commit -F <file>` command — it never runs `git commit` itself.
version: 1.0.0
---

# Commit

Standing convention on this machine: Claude never runs `git commit` directly.
Instead, `/commit` drafts a commit message, saves it to a file for the user to
review, and hands back the exact command to run. The user decides when to
actually commit.

## Steps

1. Gather context, read-only:

   ```bash
   git status --short
   git diff --staged
   git log --oneline -10
   ```

2. If `git diff --staged` is empty, stop and say so — list what's unstaged/untracked
   instead and ask the user to stage what they want committed first. Do not stage
   anything yourself (staging is the user's call) and do not draft a message for
   unstaged changes.

3. Otherwise, compose a commit message for the staged diff:
   - A single line focused on *why*, not a restatement of the diff. Add a body
     only when the *why* can't fit in one line.
   - Match the current repo's existing style (see the `git log` output above).
   - Don't hard-wrap the body to a fixed column — write each paragraph as one
     line and let the terminal/tool soft-wrap it.
   - No Claude attribution: no `Co-Authored-By: Claude` trailer, no
     "Generated with Claude Code" line.

4. Write the full message (subject + body) to
   `<repo-root>/tmp/<repo-name>-<YYYYMMDDHHMMSS>-commit.txt`:

   ```bash
   repo_root=$(git rev-parse --show-toplevel)
   repo_name=$(basename "$repo_root")
   outfile="$repo_root/tmp/${repo_name}-$(date +%Y%m%d%H%M%S)-commit.txt"
   mkdir -p "$repo_root/tmp"
   ```

   Each run gets its own timestamped file — nothing is overwritten.

5. Print:
   - The list of staged files.
   - The drafted message, in full, so the user can review it before
     committing. For small work (a few files or a few changed lines), a
     separate review step isn't needed.
   - The exact command to run:
     ```
     git commit -F <outfile>
     ```

## Notes

- Read-only except for writing the draft file — no `git add`, `git commit`, or any
  other mutating git command runs as part of this skill.
- Draft files pile up in `tmp/` over time (one per run — nothing is overwritten
  or auto-deleted). Periodic cleanup is on the user; the skill doesn't do it.
- `tmp/` lives in the repo working tree, not under `.git/`, so it needs a
  `tmp/` entry in the repo's `.gitignore` to stay out of commits. If a repo
  doesn't ignore it yet, say so before writing the file there.
- A `PreToolUse` hook in `~/.claude/settings.json` (installed by `ai/claude/install.sh`
  in danfault) backs this up by blocking any Bash command matching `git commit`
  outright, in every repo on this machine, so Claude can't bypass this skill by just
  running the command directly. It's a simple text match on the command string, so
  it can occasionally false-positive on a command whose *text* happens to contain
  the phrase "git commit" without invoking it (e.g. editing this file, or a Bash
  heredoc that echoes the block message). To remove the hard enforcement, delete
  the `git-commit-block` entry from the `PreToolUse` array in
  `~/.claude/settings.json` — the `/commit` skill still works fine without it,
  just without the hard enforcement.
