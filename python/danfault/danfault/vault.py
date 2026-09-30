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
        db: ~/path/to/main.db   # optional search index; read by obsidian-mcp
    repos:
      my-repo: { path: ~/path/to/repo, github: owner/my-repo }

CLI::

    danfault vault path [--vault NAME]        # absolute path to a vault
    danfault vault domains [--vault NAME]     # allowed note domains, one per line
    danfault vault repos [--github]           # every repo's path (or owner/repo)
    danfault vault repo NAME [--github]       # one repo's path (or owner/repo)
    danfault vault init NAME --path DIR       # create a new vault and register it
"""

import os
from pathlib import Path
from typing import List, Optional

import typer

try:
    import yaml
except ImportError:  # pragma: no cover - surfaced as a friendly error at runtime
    yaml = None

app = typer.Typer(help="Resolve vault/repo locations from ~/.config/danfault/vault.yaml")


def _config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "danfault" / "vault.yaml"


def _load(required: bool = True) -> dict:
    if yaml is None:
        typer.secho("PyYAML is not installed. Run: pip install pyyaml", fg="red", err=True)
        raise typer.Exit(1)
    path = _config_path()
    if not path.exists():
        if not required:
            return {}
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


# Folder layout the vault skills expect (/capture writes to 00-inbox/, /captains-log to 06-daily/, ...).
VAULT_FOLDERS = [
    "00-inbox",
    "01-projects",
    "02-areas",
    "03-resources",
    "04-archive",
    "06-daily",
    "07-templates",
    "08-attachments",
]

INDEXIGNORE = """\
# .indexignore
# Files and folders excluded from AI indexing (obsidian-index, obsidian_search).
# Syntax: one path per line, relative to vault root. Trailing / = folder.

# Templates contain placeholder variables — indexing them generates noise
07-templates/

# Binary files have no text content to index
08-attachments/

# Daily notes are often empty templates or low-signal logs
06-daily/

# Project session reports: high churn, stale quickly. learnings/ and status.md stay indexed.
01-projects/**/reports/

# Sensitive performance and peer review content
04-archive/feedbacks/
"""

README = """\
---
title: {name} Vault — Structure & Usage
type: moc
domain: meta
status: active
---

# {name} Vault

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `00-inbox/` | Unsorted captures pending triage. New notes land here first. |
| `01-projects/` | Project documentation. Create one with `/project-init`. |
| `02-areas/` | Ongoing responsibilities and runbooks. |
| `03-resources/` | Reference material and guides. |
| `04-archive/` | Retired material. `04-archive/feedbacks/` is excluded from the index. |
| `06-daily/` | Daily notes, named `YYYY-MM-DD`. Excluded from the index. |
| `07-templates/` | Note templates. Excluded from the index. |
| `08-attachments/` | Binary files. Excluded from the index. |

## Indexing

`.indexignore` lists the paths that the indexer skips.

## Note Frontmatter

```yaml
---
title: Note Title
type: note | project | moc | daily | resource
domain: {domains}
tags: []
status: active | archived | draft
---
```

## Retrieval Tips

- The retriever chunks at `##` (H2) boundaries. Put distinct concepts in separate H2 sections.
- Use wiki-links `[[note name]]` for human-curated relationships between notes.
"""

# Templater (https://github.com/SilentVoid13/Templater) syntax, same as the original vault templates.
TEMPLATES = {
    "Template Daily Note.md": """\
---
title: <% tp.file.creation_date("YYYY-MM-DD") %>
type: daily
tags: [daily]
status: active
---
Today I:
-
""",
    "Template Meeting.md": """\
---
title: <% tp.file.title %>
type: note
tags: [meeting]
status: active
---
<% await tp.file.rename(tp.date.now("YYYY-MM-DD") + " " + tp.file.title) %>
**Attendees**:
-

## Agenda/Questions
-

## Notes
-

## To do
-
""",
    "Template Quick Note.md": """\
---
title: <% tp.file.title %>
type: note
tags: []
status: draft
---
<% await tp.file.rename(tp.file.creation_date("YYYY-MM-DD") + " " + tp.file.title) %>
""",
}


def _write_if_missing(path: Path, content: str) -> bool:
    """Write ``content`` to ``path`` unless the file exists. Return True if written."""
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def _save_config(cfg: dict) -> None:
    """Write the config back, keeping a ``.bak`` of the previous file (safe_dump drops comments)."""
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(path.read_text())
        typer.echo(f"Backed up config to {backup}")
    path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))


@app.command()
def init(
    name: str = typer.Argument(..., help="Logical vault name to register in the config"),
    vault_path: Path = typer.Option(..., "--path", help="Directory for the vault (created if missing)"),
    domain: List[str] = typer.Option([], "--domain", help="Allowed note domain (repeatable)"),
    default: bool = typer.Option(False, "--default", help="Make this the default_vault"),
):
    """Create a vault with the standard layout and register it in the config.

    Existing files are never overwritten, so it is safe to run on an existing vault.
    Fails if NAME is already registered with a different path.
    """
    cfg = _load(required=False)
    vaults = cfg.get("vaults") or {}
    cfg["vaults"] = vaults
    root = vault_path.expanduser().resolve()

    existing = vaults.get(name)
    if existing and Path(_expand(existing.get("path", ""))).resolve() != root:
        typer.secho(f"Vault '{name}' is already registered at {existing.get('path')}.", fg="red", err=True)
        raise typer.Exit(1)

    for folder in VAULT_FOLDERS:
        (root / folder).mkdir(parents=True, exist_ok=True)
    domains_line = " | ".join(domain) if domain else "your-domain"
    files = {
        root / ".indexignore": INDEXIGNORE,
        root / "README.md": README.format(name=name, domains=domains_line),
        **{root / "07-templates" / fname: body for fname, body in TEMPLATES.items()},
    }
    for path_, content in files.items():
        state = "created" if _write_if_missing(path_, content) else "kept existing"
        typer.echo(f"{state}: {path_.relative_to(root)}")

    changed = False
    if not existing:
        entry = {"path": str(root).replace(os.path.expanduser("~"), "~", 1)}
        if domain:
            entry["domains"] = domain
        vaults[name] = entry
        changed = True
    if default or not cfg.get("default_vault"):
        changed = changed or cfg.get("default_vault") != name
        cfg["default_vault"] = name
    if changed:
        _save_config(cfg)
        typer.echo(f"Registered vault '{name}' in {_config_path()}")

    mcp_project = Path(__file__).resolve().parents[2] / "obsidian-mcp"
    typer.echo("\nNext steps:")
    typer.echo("  1. Build the search index:")
    typer.echo(f'     uv run --project "{mcp_project}" obsidian-index --vault {name} --full')
    typer.echo("  2. If not done yet on this machine, register the MCP server once (it serves every vault in the config):")
    typer.echo(f'     claude mcp add obsidian --scope user -- uv run --project "{mcp_project}" obsidian-mcp')
