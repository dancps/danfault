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
    danfault vault list projects [--status S] # projects in 01-projects/
    danfault vault tasks [--project P] [--status S]  # notes in 01-projects/*/tasks/
    danfault vault project init P [--title T] [--domain D] [--goal G] [--status S]  # create or enhance P
    danfault vault project set-status P S     # write status into P/project.json
    danfault vault health-check [--project P] # report metadata divergences
"""

import json
import os
from dataclasses import dataclass, field
from datetime import date
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
| `01-projects/` | Project documentation and tasks. Create one with `/project-init`. See [Projects and Tasks](#projects-and-tasks). |
| `02-areas/` | Ongoing responsibilities and runbooks. |
| `03-resources/` | Reference material and guides. |
| `04-archive/` | Retired material. `04-archive/feedbacks/` is excluded from the index. |
| `06-daily/` | Daily notes, named `YYYY-MM-DD`. Excluded from the index. |
| `07-templates/` | Note templates. Excluded from the index. |
| `08-attachments/` | Binary files. Excluded from the index. |

## Projects and Tasks

Each project lives in `01-projects/<project>/`. The `danfault vault` CLI reads this layout:

| Path | Purpose |
|------|---------|
| `SUMMARY.md` | Project overview. The CLI reads `title` and `status` from its frontmatter. |
| `project.json` | Optional metadata written by the CLI (for example `status`). It wins over `SUMMARY.md`. |
| `tasks/<task>.md` | One note per task, with `title`, `status` and `created` in the frontmatter. |

```bash
danfault vault list projects [--status S]        # projects, status and task count
danfault vault tasks [--project P] [--status S]  # task notes
danfault vault project init P [--title T] ...    # create a project, or add what it is missing
danfault vault project set-status P S            # write status to P/project.json
danfault vault health-check [--project P]        # divergences, missing statuses, projects without project.json
```

`set-status` does not edit `SUMMARY.md`. Update the note by hand, and use `health-check` to find what is out of sync.

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


# Projects and tasks are read from the folder layout, so existing notes need no changes:
#   01-projects/<project>/SUMMARY.md       project metadata (frontmatter, read-only)
#   01-projects/<project>/project.json     optional; written by the CLI, wins over SUMMARY.md
#   01-projects/<project>/tasks/<task>.md  one note per task (frontmatter)

PROJECT_JSON = "project.json"
PROJECT_FOLDERS = ["tasks", "learnings", "documents", "reports"]

SUMMARY_TEMPLATE = """\
---
title: {title}
type: project
domain: {domain}
tags: []
status: {status}
created: {created}
---

# {title}

**Goal:** {goal}

## Current Status

> Update this section each session.

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `tasks/` | One note per task. List them with `danfault vault tasks --project {name}` |
| `learnings/` | Reusable platform knowledge discovered during this project |
| `documents/` | Reference docs, PRDs, external material |
| `reports/` | Session outputs, validation results, analysis |

## Key Links

_(add links to PRs, notebooks, docs here)_

## Notes for Next Session

_(update before closing each session)_
"""

list_app = typer.Typer(help="List things inferred from the vault's folder structure.")
app.add_typer(list_app, name="list")
project_app = typer.Typer(help="Create projects and change their metadata (in project.json).")
app.add_typer(project_app, name="project")


def _vault_root(vault: Optional[str]) -> Path:
    _, v = _resolve_vault(_load(), vault)
    if not v.get("path"):
        typer.secho("Vault has no 'path' set.", fg="red", err=True)
        raise typer.Exit(1)
    return Path(_expand(v["path"]))


def _parse_frontmatter(path: Path) -> dict:
    """Return the frontmatter mapping ({} if the note has none). Raise ValueError if it is malformed."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError("frontmatter is not closed with ---")
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" (line {mark.line + 1})" if mark else ""
        raise ValueError(f"invalid YAML in frontmatter{where}: {getattr(e, 'problem', None) or e}") from e
    if data is not None and not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data or {}


def _frontmatter(path: Path) -> dict:
    try:
        return _parse_frontmatter(path)
    except ValueError:
        return {}


@dataclass
class _ProjectInfo:
    path: Path
    title: str = ""
    md_status: Optional[str] = None
    json_status: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return self.json_status or self.md_status or "unknown"

    @property
    def diverged(self) -> bool:
        return bool(self.json_status and self.md_status and self.json_status != self.md_status)


def _read_project_json(path: Path) -> dict:
    """Return project.json ({} if missing). Raise ValueError if it is malformed."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid {PROJECT_JSON}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"{PROJECT_JSON} is not an object")
    return data


def _read_project(path: Path) -> _ProjectInfo:
    info = _ProjectInfo(path)
    summary = path / "SUMMARY.md"
    if summary.exists():
        try:
            meta = _parse_frontmatter(summary)
            info.title = str(meta.get("title") or "")
            info.md_status = meta.get("status")
        except ValueError as e:
            info.errors.append(f"SUMMARY.md: {e}")
    try:
        info.json_status = _read_project_json(path / PROJECT_JSON).get("status")
    except ValueError as e:
        info.errors.append(str(e))
    return info


def _projects(root: Path) -> List[Path]:
    return sorted(p for p in (root / "01-projects").iterdir() if p.is_dir() and not p.name.startswith("."))


def _project(root: Path, name: str) -> Path:
    path = root / "01-projects" / name
    if not path.is_dir():
        typer.secho(f"Unknown project '{name}'. See `danfault vault list projects`.", fg="red", err=True)
        raise typer.Exit(1)
    return path


def _tasks(project: Path) -> List[Path]:
    folder = project / "tasks"
    return sorted(folder.glob("*.md")) if folder.is_dir() else []


def _print_table(headers: List[str], rows: List[List[str]]) -> None:
    widths = [max(len(str(c)) for c in col) for col in zip(headers, *rows)]
    for i, row in enumerate([headers, *rows]):
        line = "  ".join(str(c).ljust(w) for c, w in zip(row, widths)).rstrip()
        typer.secho(line, bold=i == 0)


def _warn(message: str) -> None:
    typer.secho(f"warning: {message}", fg="yellow", err=True)


def _warn_if_diverged(infos: List[_ProjectInfo]) -> None:
    names = [i.path.name for i in infos if i.diverged]
    if names:
        _warn(
            f"{PROJECT_JSON} and SUMMARY.md disagree on status for: {', '.join(names)}. "
            "See `danfault vault health-check`."
        )


@list_app.command("projects")
def list_projects(
    vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)"),
    status: Optional[str] = typer.Option(None, "--status", help="Only projects with this status"),
):
    """List projects in 01-projects/ with their status and task count."""
    infos = [_read_project(p) for p in _projects(_vault_root(vault))]
    rows = [
        [i.path.name, i.title, i.status, len(_tasks(i.path))]
        for i in infos
        if not status or i.status == status
    ]
    _print_table(["PROJECT", "TITLE", "STATUS", "TASKS"], rows)
    _warn_if_diverged(infos)


@app.command()
def tasks(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Only tasks of this project (folder name)"),
    vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)"),
    status: Optional[str] = typer.Option(None, "--status", help="Only tasks with this status"),
):
    """List task notes from 01-projects/<project>/tasks/."""
    root = _vault_root(vault)
    projects = [_project(root, project)] if project else _projects(root)
    rows = []
    for p in projects:
        for task in _tasks(p):
            meta = _frontmatter(task)
            if status and (meta.get("status") or "unknown") != status:
                continue
            rows.append([p.name, task.stem, meta.get("title", ""), meta.get("status") or "unknown", meta.get("created", "")])
    _print_table(["PROJECT", "TASK", "TITLE", "STATUS", "CREATED"], rows)
    _warn_if_diverged([_read_project(p) for p in projects])


@project_app.command("init")
def project_init(
    name: str = typer.Argument(..., help="Project folder name (kebab-case)"),
    title: Optional[str] = typer.Option(None, "--title", help="Title for a new SUMMARY.md (default: from NAME)"),
    domain: str = typer.Option("", "--domain", help="Domain for a new SUMMARY.md (one of `danfault vault domains`)"),
    goal: str = typer.Option("", "--goal", help="One-sentence goal for a new SUMMARY.md"),
    status: Optional[str] = typer.Option(None, "--status", help="Status for new files (default: SUMMARY.md's, else active)"),
    vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)"),
):
    """Create a project, or add what an existing one is missing (folders, SUMMARY.md, project.json).

    Existing files are never overwritten, so it is safe to run on an existing project to enhance it.
    """
    cfg = _load()
    _, v = _resolve_vault(cfg, vault)
    domains_cfg = v.get("domains") or []
    if domain and domains_cfg and domain not in domains_cfg:
        typer.secho(f"Unknown domain '{domain}'. Known: {', '.join(domains_cfg)}", fg="red", err=True)
        raise typer.Exit(1)
    path = _vault_root(vault) / "01-projects" / name

    info = _read_project(path) if path.is_dir() else _ProjectInfo(path)
    if info.errors:
        for e in info.errors:
            typer.secho(f"{name}: {e}", fg="red", err=True)
        raise typer.Exit(1)
    if status and (path / PROJECT_JSON).exists():
        _warn(f"--status ignored: {PROJECT_JSON} already exists. Use `danfault vault project set-status {name} {status}`.")
    if (title or domain or goal) and (path / "SUMMARY.md").exists():
        _warn("--title/--domain/--goal ignored: SUMMARY.md already exists.")
    status = status or info.md_status or "active"

    for folder in PROJECT_FOLDERS:
        if (path / folder).is_dir():
            typer.echo(f"kept existing: {folder}/")
        else:
            (path / folder).mkdir(parents=True)
            (path / folder / ".gitkeep").touch()
            typer.echo(f"created: {folder}/")
    summary = SUMMARY_TEMPLATE.format(
        name=name,
        title=title or name.replace("-", " ").title(),
        domain=domain,
        status=status,
        created=date.today().isoformat(),
        goal=goal,
    )
    files = {
        "SUMMARY.md": summary,
        PROJECT_JSON: json.dumps({"status": status}, indent=2, ensure_ascii=False) + "\n",
    }
    for fname, content in files.items():
        state = "created" if _write_if_missing(path / fname, content) else "kept existing"
        typer.echo(f"{state}: {fname}")
    if _read_project(path).diverged:
        _warn(f"{PROJECT_JSON} and SUMMARY.md disagree on status. See `danfault vault health-check --project {name}`.")


@project_app.command("set-status")
def project_set_status(
    project: str = typer.Argument(..., help="Project folder name"),
    status: str = typer.Argument(..., help="New status, e.g. active, finished"),
    vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)"),
):
    """Set a project's status in its project.json (created if missing). SUMMARY.md is not touched."""
    path = _project(_vault_root(vault), project)
    info = _read_project(path)
    try:
        data = _read_project_json(path / PROJECT_JSON)
    except ValueError as e:
        typer.secho(f"{project}: {e}. Fix it before setting the status.", fg="red", err=True)
        raise typer.Exit(1)
    data["status"] = status
    (path / PROJECT_JSON).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"{project}: {info.status} -> {status}")
    if info.md_status and info.md_status != status:
        _warn(
            f"{project}/SUMMARY.md still says status: {info.md_status}. Update it to match. "
            f"See `danfault vault health-check --project {project}`."
        )


@app.command("health-check")
def health_check(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Only check this project (folder name)"),
    vault: Optional[str] = typer.Option(None, "--vault", help="Vault name (default: default_vault)"),
):
    """Report status divergences, missing statuses and malformed metadata. Exits 1 if any issue is found.

    Also lists projects without a project.json (not yet enhanced). That list is only a guide and does not
    change the exit code.
    """
    root = _vault_root(vault)
    projects = [_project(root, project)] if project else _projects(root)
    issues = []
    not_enhanced = [p.name for p in projects if not (p / PROJECT_JSON).exists()]
    for p in projects:
        info = _read_project(p)
        issues += [(p.name, e) for e in info.errors]
        if info.diverged:
            issues.append((p.name, f"status differs: {PROJECT_JSON}={info.json_status}, SUMMARY.md={info.md_status}"))
        elif info.status == "unknown" and not info.errors:
            issues.append((p.name, f"no status in {PROJECT_JSON} or SUMMARY.md"))
        for task in _tasks(p):
            try:
                if not _parse_frontmatter(task).get("status"):
                    issues.append((p.name, f"tasks/{task.name}: no status"))
            except ValueError as e:
                issues.append((p.name, f"tasks/{task.name}: {e}"))
    if issues:
        _print_table(["PROJECT", "ISSUE"], [list(i) for i in issues])
    else:
        typer.secho("No issues found.", fg="green")
    if not_enhanced:
        typer.secho(f"\nNot enhanced yet (no {PROJECT_JSON}): {', '.join(not_enhanced)}", fg="yellow")
        typer.echo("Create it with `danfault vault project init <project>`.")
    if issues:
        raise typer.Exit(1)
