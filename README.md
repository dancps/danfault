# danfault

Personal dotfiles and tools.

## Tools

- **[coffee](docs/coffee.md)** — GUI calculator for coffee-to-water proportions, with recipe presets.
- **[spoti](docs/spoti.md)** — Spotify CLI and playlist analysis dashboard (Web API, OAuth PKCE).

## Install (Python tools)

```bash
uv tool install --editable --reinstall python/danfault
```

Registers: `danfault`, `spoti`, `coffee`, `rmatlab` in `~/.local/bin`, in their own environment. Code changes apply immediately; rerun the command after changing entry points or dependencies in `pyproject.toml`. `ai/claude/install.sh` runs it too.

## Cedilla problem
[This](https://www.danielkossmann.com/pt/ajeitando-cedilha-errado-ubuntu-linux/) fixed the problem for me in Ubuntu.