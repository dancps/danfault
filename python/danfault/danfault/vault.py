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
    danfault vault init NAME --path DIR [--github]  # create a new vault and register it
    danfault vault list projects [--status S] # projects in 01-projects/
    danfault vault tasks [--project P] [--status S]  # notes in 01-projects/*/tasks/
    danfault vault project init P [--title T] [--domain D] [--goal G] [--status S]  # create or enhance P
    danfault vault project set-status P S     # write status into P/project.json
    danfault vault task set-status P T S      # write task T's status into P/project.json
    danfault vault link V [--repo owner/repo] # link a code repo to vault V (in V/vault.json)
    danfault vault unlink V [--repo owner/repo]
    danfault vault project link P [--repo owner/repo]  # link a code repo to P (in P/project.json)
    danfault vault which                      # which vaults/project are used here, and why
    danfault vault health-check [--project P] # report metadata divergences

Without --vault, the vaults are: $DANFAULT_VAULT, else every vault linked to the current repo's
origin (vault.json or a project's project.json), else the vault that contains the current
directory, else default_vault. Read commands cover every linked vault; write commands use the
one that has the project.
"""

import json
import os
import re
import subprocess
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


def _git_remote(cwd: Path) -> Optional[str]:
    """owner/repo (lowercase) of the origin remote of the git repo at cwd, or None."""
    try:
        r = subprocess.run(["git", "-C", str(cwd), "remote", "get-url", "origin"], capture_output=True, text=True)
    except FileNotFoundError:
        return None
    m = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", r.stdout.strip()) if r.returncode == 0 else None
    return m.group(1).lower() if m else None


def _repo_arg(repo: Optional[str]) -> str:
    """The --repo value, or the current repo's origin. Exits 1 if neither is an owner/repo."""
    repo = (repo or _git_remote(Path.cwd()) or "").strip().lower()
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", repo):
        typer.secho("Not in a git repo with an origin remote. Pass --repo owner/repo.", fg="red", err=True)
        raise typer.Exit(1)
    return repo


def _repos_in(path: Path) -> List[str]:
    """Lowercase "repos" of a vault.json or project.json ([] if missing or malformed)."""
    try:
        repos_ = _read_project_json(path).get("repos") or []
    except ValueError:
        return []
    return [str(r).lower() for r in repos_] if isinstance(repos_, list) else []


def _vault_paths(cfg: dict) -> dict:
    return {n: Path(_expand(v["path"])) for n, v in (cfg.get("vaults") or {}).items() if (v or {}).get("path")}


def _linked_projects(cfg: dict, repo: str) -> List[tuple]:
    """(vault, project) pairs whose project.json lists repo in "repos"."""
    return [
        (name, pj.parent.name)
        for name, root in _vault_paths(cfg).items()
        for pj in sorted((root / "01-projects").glob(f"*/{PROJECT_JSON}"))
        if repo in _repos_in(pj)
    ]


def _linked_vaults(cfg: dict, repo: str) -> List[str]:
    """Vaults linked to repo, in config order: through <vault>/vault.json or through one of their projects."""
    by_project = {v for v, _ in _linked_projects(cfg, repo)}
    return [n for n, root in _vault_paths(cfg).items() if n in by_project or repo in _repos_in(root / VAULT_JSON)]


@dataclass
class _Context:
    vaults: List[str]
    reason: str
    project: Optional[tuple] = None
    repo: Optional[str] = None

    @property
    def vault(self) -> str:
        return self.vaults[0]


def _context(cfg: dict, name: Optional[str]) -> _Context:
    """Pick the vaults: --vault > $DANFAULT_VAULT > vaults linked to this repo > vault containing cwd > default_vault."""
    vaults = cfg.get("vaults") or {}
    cwd = Path.cwd().resolve()
    repo = _git_remote(cwd)
    inside = [n for n, root in _vault_paths(cfg).items() if cwd.is_relative_to(root.resolve())]
    linked = _linked_vaults(cfg, repo) if repo else []
    if name:
        names, reason = [name], "--vault"
    elif os.environ.get("DANFAULT_VAULT"):
        names, reason = [os.environ["DANFAULT_VAULT"]], "$DANFAULT_VAULT"
    elif linked:
        names, reason = linked, f"repo {repo} is linked to it"
    elif inside:
        names, reason = inside[:1], "the current directory is inside it"
    else:
        names, reason = [cfg.get("default_vault")], "default_vault"
    if not names[0]:
        typer.secho("No vault specified and no default_vault in config.", fg="red", err=True)
        raise typer.Exit(1)
    for n in names:
        if n not in vaults:
            typer.secho(f"Unknown vault '{n}'. Known: {', '.join(vaults) or '(none)'}", fg="red", err=True)
            raise typer.Exit(1)
    projects = [(v, p) for v, p in _linked_projects(cfg, repo) if v in names] if repo else []
    if len(projects) > 1:
        listed = ", ".join(f"{v}/{p}" for v, p in projects)
        _warn(f"repo {repo} is linked to several projects ({listed}); using {projects[0][1]}.")
    project = projects[0] if projects else None
    if not project and names[0] in inside:
        rel = cwd.relative_to(_vault_paths(cfg)[names[0]].resolve()).parts
        if len(rel) >= 2 and rel[0] == "01-projects":
            project = (names[0], rel[1])
    return _Context(names, reason, project, repo)


def _resolve_vault(cfg: dict, name: Optional[str]) -> tuple[str, dict]:
    """The single vault for commands that use one. Warns when the repo is linked to several."""
    ctx = _context(cfg, name)
    if len(ctx.vaults) > 1:
        _warn(f"repo {ctx.repo} is linked to several vaults ({', '.join(ctx.vaults)}); using {ctx.vault}. Pass --vault.")
    return ctx.vault, cfg["vaults"][ctx.vault] or {}


def _roots(vault: Optional[str]) -> dict:
    """{vault name: root} of every vault a read command covers."""
    cfg = _load()
    paths = _vault_paths(cfg)
    names = _context(cfg, vault).vaults
    missing = [n for n in names if n not in paths]
    if missing:
        typer.secho(f"Vault '{missing[0]}' has no 'path' set.", fg="red", err=True)
        raise typer.Exit(1)
    return {n: paths[n] for n in names}


def _project_root(vault: Optional[str], project: str, new: bool = False) -> tuple[str, Path]:
    """(vault, project folder) for a write command: the one covered vault that has the project.

    With new=True and several covered vaults, the project must not need guessing: --vault is required.
    """
    roots = _roots(vault)
    if len(roots) == 1:
        name, root = next(iter(roots.items()))
        return name, (root / "01-projects" / project if new else _project(root, project))
    found = [n for n, r in roots.items() if (r / "01-projects" / project).is_dir()]
    if len(found) == 1:
        return found[0], roots[found[0]] / "01-projects" / project
    where = f"in several vaults ({', '.join(found)})" if found else f"in none of {', '.join(roots)}"
    typer.secho(f"Project '{project}' is {where}. Pass --vault.", fg="red", err=True)
    raise typer.Exit(1)


def _vault_option(help_: str = "Vault name (default: see `danfault vault which`)"):
    return typer.Option(None, "--vault", help=help_)


@app.command()
def path(vault: Optional[str] = _vault_option()):
    """Print the absolute path to a vault."""
    _, v = _resolve_vault(_load(), vault)
    if not v.get("path"):
        typer.secho("Vault has no 'path' set.", fg="red", err=True)
        raise typer.Exit(1)
    typer.echo(_expand(v["path"]))


@app.command()
def which(vault: Optional[str] = _vault_option()):
    """Show which vaults and project commands use here, and why.

    Vault order: --vault, $DANFAULT_VAULT, the vaults linked to this git repo's origin (in <vault>/vault.json
    or in a project's project.json), the vault that contains the current directory, default_vault.
    """
    cfg = _load()
    ctx = _context(cfg, vault)
    paths = _vault_paths(cfg)
    for n in ctx.vaults:
        typer.echo(f"vault:   {n} ({paths.get(n, '-')})")
    typer.echo(f"reason:  {ctx.reason}")
    typer.echo(f"project: {'/'.join(ctx.project) if ctx.project else '-'}")
    typer.echo(f"repo:    {ctx.repo or '-'}")


@app.command()
def link(
    vault: str = typer.Argument(..., help="Vault name"),
    repo: Optional[str] = typer.Option(None, "--repo", help="owner/repo (default: origin of the current git repo)"),
):
    """Link a code repo to a vault (adds it to "repos" in <vault>/vault.json). A repo can be linked to several vaults.

    Inside that repo, commands then use the linked vaults. Nothing is written to the repo.
    """
    root = _vault_root(vault)
    repo = _repo_arg(repo)
    try:
        data = _read_project_json(root / VAULT_JSON)
    except ValueError as e:
        typer.secho(f"{vault}: {e}. Fix it before linking.", fg="red", err=True)
        raise typer.Exit(1)
    repos_ = data.setdefault("repos", [])
    if not isinstance(repos_, list):
        typer.secho(f'{vault}: "repos" in {VAULT_JSON} is not a list. Fix it before linking.', fg="red", err=True)
        raise typer.Exit(1)
    if repo in [str(r).lower() for r in repos_]:
        typer.echo(f"{vault}: already linked to {repo}")
        return
    repos_.append(repo)
    (root / VAULT_JSON).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"{vault}: linked to {repo}")


@app.command()
def unlink(
    vault: str = typer.Argument(..., help="Vault name"),
    repo: Optional[str] = typer.Option(None, "--repo", help="owner/repo (default: origin of the current git repo)"),
):
    """Remove a code repo from "repos" in <vault>/vault.json. Project links (project.json) are kept."""
    root = _vault_root(vault)
    repo = _repo_arg(repo)
    try:
        data = _read_project_json(root / VAULT_JSON)
    except ValueError as e:
        typer.secho(f"{vault}: {e}. Fix it before unlinking.", fg="red", err=True)
        raise typer.Exit(1)
    repos_ = data.get("repos")
    kept = [r for r in repos_ if str(r).lower() != repo] if isinstance(repos_, list) else repos_
    if kept == repos_:
        typer.echo(f"{vault}: {repo} is not in {VAULT_JSON}")
    else:
        data["repos"] = kept
        (root / VAULT_JSON).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        typer.echo(f"{vault}: unlinked {repo}")
    projects = [p for v, p in _linked_projects(_load(), repo) if v == vault]
    if projects:
        _warn(f"{repo} is still linked to {vault} through project(s) {', '.join(projects)} (project.json).")


@app.command()
def domains(vault: Optional[str] = _vault_option()):
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
| `project.json` | Optional metadata written by the CLI: the project's `status`, a `tasks` map of task statuses and the linked code `repos`. It wins over the notes. |
| `tasks/<task>.md` | One note per task, with `title`, `status` and `created` in the frontmatter. |

```bash
danfault vault list projects [--status S]        # projects, status and task count
danfault vault tasks [--project P] [--status S]  # task notes
danfault vault project init P [--title T] ...    # create a project, or add what it is missing
danfault vault project set-status P S            # write status to P/project.json
danfault vault task set-status P T S             # write task T's status to P/project.json
danfault vault link V                            # link the current code repo to vault V (V/vault.json)
danfault vault project link P                    # link the current code repo to P
danfault vault which                             # vault and project used in the current directory
danfault vault health-check [--project P]        # divergences, missing statuses, projects without project.json
```

`set-status` does not edit `SUMMARY.md` or task notes. Update the note by hand, and use `health-check` to find what is out of sync.

**Syncing:** Obsidian Sync skips `project.json` (not a note) and dot-files (`.indexignore`, `.gitkeep`). Back the vault up with git (Obsidian Git plugin); run `/obsidian-vault:vault-git-setup` to set it up. If you rely only on Sync, turn on *Settings → Sync → Selective sync → Sync all other types* on every device.

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


GITIGNORE = """\
.obsidian/workspace*.json
.obsidian/cache
.trash/
"""


def _run(*cmd: str, cwd: Optional[Path] = None) -> str:
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    except FileNotFoundError:
        typer.secho(f"`{cmd[0]}` is not installed.", fg="red", err=True)
        raise typer.Exit(1)
    if result.returncode != 0:
        typer.secho(f"`{' '.join(cmd)}` failed: {result.stderr.strip()}", fg="red", err=True)
        raise typer.Exit(1)
    return result.stdout.strip()


def _setup_github(root: Path, repo: str) -> None:
    """git init the vault and link a private GitHub repo as origin. Never commits."""
    state = "created" if _write_if_missing(root / ".gitignore", GITIGNORE) else "kept existing"
    typer.echo(f"{state}: .gitignore")
    if (root / ".git").exists():
        typer.echo("kept existing: .git")
    else:
        _run("git", "init", "-b", "main", cwd=root)
        typer.echo("created: .git (branch main)")
    if "origin" in _run("git", "remote", cwd=root).split():
        url = _run("git", "remote", "get-url", "origin", cwd=root)
        typer.echo(f"kept existing: remote origin ({url})")
        return
    owner = _run("gh", "api", "user", "--jq", ".login")
    if subprocess.run(["gh", "repo", "view", f"{owner}/{repo}"], capture_output=True).returncode == 0:
        typer.echo(f"kept existing: GitHub repo {owner}/{repo}")
    else:
        _run("gh", "repo", "create", repo, "--private")
        typer.echo(f"created: private GitHub repo {owner}/{repo}")
    # SSH, so the Flatpak Obsidian can push with the host's ssh-agent.
    _run("git", "remote", "add", "origin", f"git@github.com:{owner}/{repo}.git", cwd=root)
    typer.echo(f"added: remote origin git@github.com:{owner}/{repo}.git")


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
    github: bool = typer.Option(
        False, "--github", help="Also git init the vault and create a private GitHub repo NAME-obsidian-vault as origin"
    ),
):
    """Create a vault with the standard layout and register it in the config.

    Existing files are never overwritten, so it is safe to run on an existing vault.
    Fails if NAME is already registered with a different path.
    With --github, also adds a .gitignore, runs git init and links a private GitHub repo. It never commits.
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

    if github:
        _setup_github(root, f"{name}-obsidian-vault")

    mcp_project = Path(__file__).resolve().parents[2] / "obsidian-mcp"
    typer.echo("\nNext steps:")
    typer.echo("  1. Build the search index:")
    typer.echo(f'     uv run --project "{mcp_project}" obsidian-index --vault {name} --full')
    typer.echo("  2. If not done yet on this machine, register the MCP server once (it serves every vault in the config):")
    typer.echo(f'     claude mcp add obsidian --scope user -- uv run --project "{mcp_project}" obsidian-mcp')
    if github:
        typer.echo("  3. Scan for secrets, then make the first commit and push:")
        typer.echo(f"     cd \"{root}\" && uvx detect-secrets scan --all-files --exclude-files '^\\.git/' .")
        typer.echo("     git add -A && git commit -m 'vault: initial commit' && git push -u origin main")
        typer.echo("  4. Set up the Obsidian Git plugin: /obsidian-vault:vault-git-setup")


# Projects and tasks are read from the folder layout, so existing notes need no changes:
#   01-projects/<project>/SUMMARY.md       project metadata (frontmatter, read-only)
#   01-projects/<project>/project.json     optional; written by the CLI, wins over SUMMARY.md
#   01-projects/<project>/tasks/<task>.md  one note per task (frontmatter)

PROJECT_JSON = "project.json"
VAULT_JSON = "vault.json"
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
task_app = typer.Typer(help="Change a task's metadata (in its project's project.json).")
app.add_typer(task_app, name="task")


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
    json_tasks: dict = field(default_factory=dict)
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
        data = _read_project_json(path / PROJECT_JSON)
        info.json_status = data.get("status")
        tasks_ = data.get("tasks", {})
        if isinstance(tasks_, dict):
            info.json_tasks = tasks_
        else:
            info.errors.append(f'{PROJECT_JSON}: "tasks" is not an object')
        repos_ = data.get("repos", [])
        if not isinstance(repos_, list) or not all(isinstance(r, str) for r in repos_):
            info.errors.append(f'{PROJECT_JSON}: "repos" is not a list of "owner/repo" strings')
    except ValueError as e:
        info.errors.append(str(e))
    return info


def _task_status(info: _ProjectInfo, task: Path) -> str:
    return info.json_tasks.get(task.stem) or _frontmatter(task).get("status") or "unknown"


def _task_divergences(info: _ProjectInfo) -> List[tuple]:
    """(task id, project.json status, frontmatter status) for each task whose two statuses differ."""
    out = []
    for task in _tasks(info.path):
        json_status, md_status = info.json_tasks.get(task.stem), _frontmatter(task).get("status")
        if json_status and md_status and json_status != md_status:
            out.append((task.stem, json_status, md_status))
    return out


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
    names += [f"{i.path.name}/{t}" for i in infos for t, _, _ in _task_divergences(i)]
    if names:
        _warn(
            f"{PROJECT_JSON} and the notes disagree on status for: {', '.join(names)}. "
            "See `danfault vault health-check`."
        )


def _selected(vault: Optional[str], project: Optional[str]) -> List[tuple]:
    """(vault, project folder) pairs a read command covers: every project of the covered vaults, or one project."""
    roots = _roots(vault)
    if not project:
        return [(n, p) for n, r in roots.items() for p in _projects(r)]
    found = [(n, r / "01-projects" / project) for n, r in roots.items() if (r / "01-projects" / project).is_dir()]
    if not found:
        typer.secho(f"Unknown project '{project}'. See `danfault vault list projects`.", fg="red", err=True)
        raise typer.Exit(1)
    return found


def _with_vault(headers: List[str], rows: List[list], vault_names: List[str], multi: bool) -> tuple:
    """Add a VAULT column when the command covers several vaults."""
    if not multi:
        return headers, rows
    return ["VAULT", *headers], [[v, *r] for v, r in zip(vault_names, rows)]


@list_app.command("projects")
def list_projects(
    vault: Optional[str] = _vault_option(),
    status: Optional[str] = typer.Option(None, "--status", help="Only projects with this status"),
):
    """List projects in 01-projects/ with their status and task count. A repo linked to several vaults lists all."""
    selected = _selected(vault, None)
    infos = [(v, _read_project(p)) for v, p in selected]
    kept = [(v, i) for v, i in infos if not status or i.status == status]
    rows = [[i.path.name, i.title, i.status, len(_tasks(i.path))] for _, i in kept]
    multi = len({v for v, _ in selected}) > 1
    _print_table(*_with_vault(["PROJECT", "TITLE", "STATUS", "TASKS"], rows, [v for v, _ in kept], multi))
    _warn_if_diverged([i for _, i in infos])


@app.command()
def tasks(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Only tasks of this project (folder name)"),
    vault: Optional[str] = _vault_option(),
    status: Optional[str] = typer.Option(None, "--status", help="Only tasks with this status"),
    all_: bool = typer.Option(False, "--all", help="Every project, even inside a repo linked to a project"),
):
    """List task notes from 01-projects/<project>/tasks/. A status in project.json wins over the note's.

    Without --project, a repo linked to a project (or a project folder) shows only that project's tasks.
    """
    ctx = _context(_load(), vault)
    if not project and not all_ and ctx.project:
        vault, project = ctx.project
        typer.secho(f"Showing project {project} (see `danfault vault which`). Use --all for every project.", err=True)
    selected = _selected(vault, project)
    infos = [(v, _read_project(p)) for v, p in selected]
    rows, names = [], []
    for v, info in infos:
        for task in _tasks(info.path):
            meta = _frontmatter(task)
            task_status = _task_status(info, task)
            if status and task_status != status:
                continue
            rows.append([info.path.name, task.stem, meta.get("title", ""), task_status, meta.get("created", "")])
            names.append(v)
    multi = len({v for v, _ in selected}) > 1
    _print_table(*_with_vault(["PROJECT", "TASK", "TITLE", "STATUS", "CREATED"], rows, names, multi))
    _warn_if_diverged([i for _, i in infos])


@project_app.command("init")
def project_init(
    name: str = typer.Argument(..., help="Project folder name (kebab-case)"),
    title: Optional[str] = typer.Option(None, "--title", help="Title for a new SUMMARY.md (default: from NAME)"),
    domain: str = typer.Option("", "--domain", help="Domain for a new SUMMARY.md (one of `danfault vault domains`)"),
    goal: str = typer.Option("", "--goal", help="One-sentence goal for a new SUMMARY.md"),
    status: Optional[str] = typer.Option(None, "--status", help="Status for new files (default: SUMMARY.md's, else active)"),
    vault: Optional[str] = _vault_option(),
):
    """Create a project, or add what an existing one is missing (folders, SUMMARY.md, project.json).

    Existing files are never overwritten, so it is safe to run on an existing project to enhance it.
    In a repo linked to several vaults, a new project needs --vault.
    """
    vault_name, path = _project_root(vault, name, new=True)
    domains_cfg = (_load()["vaults"][vault_name] or {}).get("domains") or []
    if domain and domains_cfg and domain not in domains_cfg:
        typer.secho(f"Unknown domain '{domain}'. Known: {', '.join(domains_cfg)}", fg="red", err=True)
        raise typer.Exit(1)

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

    typer.echo(f"vault: {vault_name}")
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
    vault: Optional[str] = _vault_option(),
):
    """Set a project's status in its project.json (created if missing). SUMMARY.md is not touched."""
    _, path = _project_root(vault, project)
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


@project_app.command("link")
def project_link(
    project: str = typer.Argument(..., help="Project folder name"),
    repo: Optional[str] = typer.Option(None, "--repo", help="owner/repo (default: origin of the current git repo)"),
    vault: Optional[str] = _vault_option(),
):
    """Link a code repo to a project (adds it to "repos" in project.json). This also links the repo to the vault.

    Inside that repo, `tasks` then shows this project. Nothing is written to the repo.
    """
    vault_name, path = _project_root(vault, project)
    repo = _repo_arg(repo)
    info = _read_project(path)
    if info.errors:
        for e in info.errors:
            typer.secho(f"{project}: {e}. Fix it before linking.", fg="red", err=True)
        raise typer.Exit(1)
    others = [f"{v}/{p}" for v, p in _linked_projects(_load(), repo) if (v, p) != (vault_name, project)]
    data = _read_project_json(path / PROJECT_JSON)
    repos_ = data.setdefault("repos", [])
    if repo in [r.lower() for r in repos_]:
        typer.echo(f"{vault_name}/{project}: already linked to {repo}")
    else:
        repos_.append(repo)
        (path / PROJECT_JSON).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        typer.echo(f"{vault_name}/{project}: linked to {repo}")
    if others:
        _warn(f"{repo} is also linked to {', '.join(others)}. In that repo, `tasks` uses the first one found.")


@task_app.command("set-status")
def task_set_status(
    project: str = typer.Argument(..., help="Project folder name"),
    task: str = typer.Argument(..., help="Task id (file name in tasks/, without .md)"),
    status: str = typer.Argument(..., help="New status, e.g. open, done, blocked"),
    vault: Optional[str] = _vault_option(),
):
    """Set a task's status in its project's project.json (created if missing). The task note is not touched."""
    _, path = _project_root(vault, project)
    note = path / "tasks" / f"{task}.md"
    if not note.exists():
        typer.secho(f"Unknown task '{task}'. See `danfault vault tasks --project {project}`.", fg="red", err=True)
        raise typer.Exit(1)
    info = _read_project(path)
    if info.errors:
        for e in info.errors:
            typer.secho(f"{project}: {e}. Fix it before setting the status.", fg="red", err=True)
        raise typer.Exit(1)
    data = _read_project_json(path / PROJECT_JSON)
    old = _task_status(info, note)
    data.setdefault("tasks", {})[task] = status
    (path / PROJECT_JSON).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    typer.echo(f"{project}/{task}: {old} -> {status}")
    md_status = _frontmatter(note).get("status")
    if md_status and md_status != status:
        _warn(
            f"{project}/tasks/{task}.md still says status: {md_status}. Update it to match. "
            f"See `danfault vault health-check --project {project}`."
        )


@app.command("health-check")
def health_check(
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Only check this project (folder name)"),
    vault: Optional[str] = _vault_option(),
):
    """Report status divergences, missing statuses and malformed metadata. Exits 1 if any issue is found.

    Also lists projects without a project.json (not yet enhanced). That list is only a guide and does not
    change the exit code.
    """
    roots = _roots(vault)
    selected = _selected(vault, project)
    multi = len(roots) > 1
    label = (lambda v, name: f"{v}/{name}") if multi else (lambda v, name: name)
    issues = []
    if not project:
        for v, root in roots.items():
            if (root / VAULT_JSON).exists():
                try:
                    repos_ = _read_project_json(root / VAULT_JSON).get("repos", [])
                    if not isinstance(repos_, list) or not all(isinstance(r, str) for r in repos_):
                        issues.append((label(v, VAULT_JSON), '"repos" is not a list of "owner/repo" strings'))
                except ValueError as e:
                    issues.append((label(v, VAULT_JSON), str(e).replace(PROJECT_JSON, VAULT_JSON)))
    not_enhanced = [label(v, p.name) for v, p in selected if not (p / PROJECT_JSON).exists()]
    for v, p in selected:
        name = label(v, p.name)
        info = _read_project(p)
        issues += [(name, e) for e in info.errors]
        if info.diverged:
            issues.append((name, f"status differs: {PROJECT_JSON}={info.json_status}, SUMMARY.md={info.md_status}"))
        elif info.status == "unknown" and not info.errors:
            issues.append((name, f"no status in {PROJECT_JSON} or SUMMARY.md"))
        task_files = _tasks(p)
        for task in task_files:
            try:
                if not (info.json_tasks.get(task.stem) or _parse_frontmatter(task).get("status")):
                    issues.append((name, f"tasks/{task.name}: no status"))
            except ValueError as e:
                issues.append((name, f"tasks/{task.name}: {e}"))
        for t, json_status, md_status in _task_divergences(info):
            issues.append((name, f"tasks/{t}.md: status differs: {PROJECT_JSON}={json_status}, note={md_status}"))
        existing = {t.stem for t in task_files}
        for t in sorted(set(info.json_tasks) - existing):
            issues.append((name, f'{PROJECT_JSON} has task "{t}" but tasks/{t}.md does not exist'))
    if issues:
        _print_table(["PROJECT", "ISSUE"], [list(i) for i in issues])
    else:
        typer.secho("No issues found.", fg="green")
    if not_enhanced:
        typer.secho(f"\nNot enhanced yet (no {PROJECT_JSON}): {', '.join(not_enhanced)}", fg="yellow")
        typer.echo("Create it with `danfault vault project init <project>`.")
    if issues:
        raise typer.Exit(1)
