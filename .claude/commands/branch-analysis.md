# Branch Divergence Analysis

You are performing a deep git branch divergence analysis for this repo. Follow each step precisely, then present the results in the structured format below.

## Step 1: Ensure SSH credentials and fetch

Run:

```bash
ssh-add -l 2>&1
```

- If `~/.ssh/id_ed25519_gh` is listed: proceed to fetch.
- If it is NOT listed but the agent is running: tell the user to run `ssh-add ~/.ssh/id_ed25519_gh` (the GitHub key required for this repo) and then re-invoke the skill.
- If the agent has no identities or is not running: list available keys with `ls ~/.ssh/*.pub 2>/dev/null`, identify the GitHub key (`id_ed25519_gh`), and ask the user to load it with `ssh-add <key>` before continuing.

Then fetch:

```bash
git fetch --all 2>&1
```

If the fetch still fails with an authentication error, stop and ask the user to add the correct SSH key.

Then run all of these in parallel:

```bash
git branch -a
```
```bash
git log --oneline --all --graph
```
```bash
git log --oneline origin/master..$(git branch --show-current) 2>/dev/null
```

Then, for each remote branch that is NOT `origin/master`, `origin/HEAD`, `origin/feature/unix`, `origin/feature/unix2`, `origin/logs` (already merged), compute:

```bash
git log --oneline origin/master..<branch>
git diff origin/master...<branch> --stat
git merge-tree --write-tree origin/master <branch> 2>&1
```

Run all branch checks in parallel.

## Step 2: Assess local sync state

Check whether local tracking branches (`master`, `main`, current branch) are behind `origin/master`:

```bash
git log --oneline master..origin/master 2>/dev/null | wc -l
git log --oneline main..origin/master 2>/dev/null | wc -l
```

## Step 3: For every branch with unmerged commits

- List all files it touches vs `origin/master` (`git diff origin/master...<branch> --name-only`)
- Run `git merge-tree --write-tree origin/master <branch>` and capture any `CONFLICT` lines
- For each conflicting file, show: the master version (`git show origin/master:<file>`) and the branch version (`git show <branch>:<file>`) side by side, summarising the semantic difference in one sentence

## Step 4: Present the analysis

Output the following sections **in this exact format**:

---

### Local sync state

State whether local `master`/`main` are behind `origin/master` and by how many commits. Flag it clearly if they need a fast-forward pull before anything else.

---

### Branches already merged into origin/master

List any branches whose commits are fully contained in `origin/master`. One line each: branch name + what it added.

---

### Branches still unmerged

For each unmerged branch, a block:

```
#### <branch-name>
Commits ahead: N
Files touched: <list>
Conflict risk: None | Low | High
<If conflicts: describe each conflict file, what each side has, and the recommended resolution>
<If no conflicts: "Clean merge — no conflicts expected.">
```

---

### Merge plan

Propose a merge order. For each step:
- Branch name
- Why it comes first (dependencies, conflict risk, size)
- What to expect (auto-merge vs manual resolution required)
- For manual resolutions: exact resolution instructions (which side to keep, what to reconcile)

---

### Shell script offer

After the full analysis, ask the user:

> Would you like me to write a shell script that performs these merges in the proposed order, pausing at conflicts with instructions?

**Never write the script or run any merge commands unless the user explicitly confirms.**

If the user says yes, write a shell script (do not run it) that:
- Sets `set -e` and prints each step before executing
- Does `git fetch --all` first
- Fast-forwards local tracking branches if needed
- Merges each branch in the proposed order
- For branches with known conflicts: after the merge attempt, prints clear instructions for each conflict file (what to keep, what to discard) and exits with a non-zero code so the user can resolve manually before re-running
- At the end, optionally pushes to origin (gated behind a `--push` flag)

Save the script to `scripts/merge-branches.sh` (do not execute it). Tell the user to review it before running.
