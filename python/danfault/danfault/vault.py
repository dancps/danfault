"""Resolve vault and repo locations from a machine-local config file.

Skills and other tools reference logical names (a vault, a work repo) instead of
hardcoding personal paths. The real paths live in a per-machine config that is
**never committed**:

    ~/.config/danfault/vault.yaml   (or $XDG_CONFIG_HOME/danfault/vault.yaml)

Schema::

    default_vault: main
    vaults:
      main:
        path: ~/path/to/vault
        domains: [domain-a, domain-b, personal]
    repos:
      my-repo: { path: ~/path/to/repo, github: owner/my-repo }

CLI::

    danfault vault path [--vault NAME]        # absolute path to a vault
    danfault vault domains [--vault NAME]     # allowed note domains, one per line
    danfault vault repos [--github]           # every repo's path (or owner/repo)
    danfault vault repo NAME [--github]       # one repo's path (or owner/repo)
"""

import os
from pathlib import Path
from typing import Optional

import typer

try:
    import yaml
except ImportError:  # pragma: no cover - surfaced as a friendly error at runtime
    yaml = None

app = typer.Typer(help="Resolve vault/repo locations from ~/.config/danfault/vault.yaml")


def _config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "danfault" / "vault.yaml"


def _load() -> dict:
    if yaml is None:
        typer.secho("PyYAML is not installed. Run: pip install pyyaml", fg="red", err=True)
        raise typer.Exit(1)
    path = _config_path()
    if not path.exists():
        typer.secho(f"Config not found: {path}", fg="red", err=True)
        typer.secho("Create it — see `danfault vault --help` for the schema.", err=True)
        raise typer.Exit(1)
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        typer.secho(f"Malformed config (expected a mapping): {path}", fg="red", err=True)
        raise typer.Exit(1)
    return data


def _expand(p: str) -> str:
    return os.path.expanduser(str(p))


def _resolve_vault(cfg: dict, name: Optional[str]) -> tuple[str, dict]:
    vaults = cfg.get("vaults") or {}
    name = name or cfg.get("default_vault")
    if not name:
        typer.secho("No vault specified and no default_vault in config.", fg="red", err=True)
        raise typer.Exit(1)
    if name not in vaults:
        typer.secho(f"Unknown vault '{name}'. Known: {', '.join(vaults) or '(none)'}", fg="red", err=True)
        raise typer.Exit(1)
    return name, vaults[name] or {}


@app.command()
def path(vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)")):
    """Print the absolute path to a vault."""
    cfg = _load()
    _, v = _resolve_vault(cfg, vault)
    if not v.get("path"):
        typer.secho("Vault has no 'path' set.", fg="red", err=True)
        raise typer.Exit(1)
    typer.echo(_expand(v["path"]))


@app.command()
def domains(vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)")):
    """Print a vault's declared domains, one per line."""
    cfg = _load()
    _, v = _resolve_vault(cfg, vault)
    for d in v.get("domains") or []:
        typer.echo(d)


@app.command()
def repos(github: bool = typer.Option(False, "--github", help="Print owner/repo slugs instead of paths")):
    """Print every configured repo (path, or slug with --github), one per line."""
    cfg = _load()
    for name, meta in (cfg.get("repos") or {}).items():
        meta = meta or {}
        value = meta.get("github") if github else meta.get("path")
        if value:
            typer.echo(value if github else _expand(value))


@app.command()
def repo(
    name: str = typer.Argument(..., help="Repo name as declared in config"),
    github: bool = typer.Option(False, "--github", help="Print the owner/repo slug instead of the path"),
):
    """Print one repo's path (or its owner/repo slug with --github)."""
    cfg = _load()
    repos_cfg = cfg.get("repos") or {}
    if name not in repos_cfg:
        typer.secho(f"Unknown repo '{name}'. Known: {', '.join(repos_cfg) or '(none)'}", fg="red", err=True)
        raise typer.Exit(1)
    meta = repos_cfg[name] or {}
    value = meta.get("github") if github else meta.get("path")
    if not value:
        field = "github" if github else "path"
        typer.secho(f"Repo '{name}' has no '{field}' set.", fg="red", err=True)
        raise typer.Exit(1)
    typer.echo(value if github else _expand(value))
