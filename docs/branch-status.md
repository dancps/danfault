# Branch Status

> Last updated: 2026-07-01

## Uncommitted work being organized (stacked off `feature/upgrades_macos`)

A large batch of new tools was sitting uncommitted in the working tree. It is being
split into stacked feature branches (each builds on the previous so the `.gitignore`
rules apply throughout). Merge into `master` in order.

| Order | Branch | Contents |
|-------|--------|----------|
| 1 | `chore/repo-meta` | `.gitignore` (ignore `node_modules/`, `obsidian-mcp/data/`), `.claude/` config + skills, docs |
| 2 | `feature/danfault-cli-tools` | `arc` (folder→markdown) + `spotify` CLI, `spoti-ui/` dashboard, docs, `examples/spotify/` |
| 3 | `feature/shell-helpers` | `dotfiles/.methods` — `find-folder`, `find-file` |
| 4 | `feature/terminal-configs` | `terminal-configs/` backup/restore scripts |
| 5 | `feature/mermaid-extract` | `python/mermaid-extract/` typer CLI package |
| 6 | `feature/obsidian-mcp` | `python/obsidian-mcp/` vault search server (index data is gitignored) |

### Notes
- `spoti-ui/node_modules/` and `obsidian-mcp/data/` are gitignored (72 MB deps / 7 MB
  index of plaintext note chunks — regenerable, not committed).
- `main.py` imports both `arc` and `spotify`, so those two land together (branch 2).

---

## Pre-existing branches (from 2026-04-26 review)

| Branch | Commits ahead of master | What it contains | Notes |
|--------|------------------------|-----------------|-------|
| `feature/upgrades_macos` | 3 | dotfiles, python/danfault, latex, setup | Base for the stack above; merge first |
| `origin/patch/change_in_utils` | 1 | Small util additions | Quick patch |
| `origin/fearture/module_manager` | 3 | Module validator/manager feature | Check if complete |
| `origin/feature/job` | 3 | Git configs + job-related setup | Review before merging |

### Fully merged — safe to delete
`origin/feature/unix`, `origin/feature/unix2`, `origin/logs`

---

## `main` vs `master`
`main` and `master` diverged (1 commit each). `main`'s unique commit (`Includes new
features`) is already in `feature/upgrades_macos`, so `main` can be deleted once the
stack is merged.
