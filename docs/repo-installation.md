# Repo installation — open work

Status: to plan. Written 2026-09-30, while fixing a stale `danfault` CLI install that broke the Obsidian vault skills.

## Problem

There is no single way to install this repo on a machine. Each part installs itself differently, and some parts are only documented, not scripted. The `danfault` Python package is currently treated as one module among others, not as the entry point for setting up the repo.

## Current state

| Part | How it is installed today |
|---|---|
| Shell dotfiles, OS setup | `setup/setup.sh` (sources `setup/base_env.sh`, `setup/utils.sh`, `<os>/os_envs.sh`) |
| Claude Code config (`CLAUDE.md`, output style, status line, commit skill, hooks) | `ai/claude/install.sh` — links into `~/.claude`, merges `settings.json` |
| Claude plugins (`danfault-plugins`) | `ai/claude/install.sh` registers the marketplace; plugins are installed by hand with `/plugin install` |
| `danfault` CLI (`danfault`, `spoti`, `coffee`, `rmatlab`) | `uv tool install --editable --reinstall python/danfault`, run by `ai/claude/install.sh` because the vault skills need it (after `feature/obsidian-mcp-multivault`). Before that: `pip install -e .` into whatever env was active (conda on this machine). |
| `obsidian-mcp` server, indexer, capture | Not installed; always run with `uv run --project python/obsidian-mcp …`. The MCP server is registered by hand with `claude mcp add obsidian …`. |
| Vault config | `~/.config/danfault/vault.yaml`, created by `danfault vault init` |
| VS Code | `vscode/vscode_config.py` |

## Known issues

- The `danfault` CLI is installed from `ai/claude/install.sh`, which is the Claude config installer. It lives there only because the vault skills depend on it.
- `python/danfault/pyproject.toml` does not declare everything it imports: `matplotlib`, `toml` and `rich` (used by `dancompare.py` and `modules/module_validator.py`) are missing. Only `typer` and `pandas` were added, because the CLI imports them at startup.
- A machine set up before the switch to `uv tool` can have a second `danfault` in a conda env. Which one runs depends on `PATH` order.
- `README.md` documents only the Python tools install.

## Questions to decide

1. One top-level entry point (for example `./install.sh` or `setup/setup.sh`) that calls each part's installer, or keep the per-part installers and document the order?
2. Should the `danfault` CLI own setup (for example `danfault setup claude`, `danfault setup vault`), or stay a module installed by the scripts?
3. Should `obsidian-mcp` be installed as a `uv tool` too, or keep `uv run --project`?
4. Which steps must be non-interactive for a fresh machine (see `ai/claude/install.sh --yes`)?
5. Should registering the `obsidian` MCP server and installing the plugins be scripted?
