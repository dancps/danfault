"""Export Arc browser sidebar folders/spaces to Markdown link lists.

Arc stores its sidebar (spaces, folders, tabs) in an undocumented JSON file,
``StorableSidebar.json`` — not the live tab API — so this reads that file from
disk and rebuilds the tree. The original file is never modified; parsing works
on a temp copy.

CLI (wired into the main ``danfault`` app under ``arc``)::

    danfault arc tabs list
    danfault arc tabs backup ["Folder Name"] [--space ..] [--out ..] [--clipboard] [--headings] [--file ..]

The parsing layer below is pure standard library; only the CLI uses Typer.
"""

import glob
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import typer

from danfault.logs import Loggir

log = Loggir()

# ──────────────────────────────────────────────────────────────────────────
# File location
# ──────────────────────────────────────────────────────────────────────────


def _candidate_paths() -> List[Path]:
    """Return the platform-specific locations to search for StorableSidebar.json."""
    system = platform.system()
    if system == "Darwin":
        return [Path.home() / "Library" / "Application Support" / "Arc" / "StorableSidebar.json"]
    if system == "Windows":
        local = os.environ.get("LOCALAPPDATA", "")
        pattern = os.path.join(
            local,
            "Packages",
            "TheBrowserCompany.Arc_*",
            "LocalCache",
            "Local",
            "Arc",
            "StorableSidebar.json",
        )
        return [Path(p) for p in glob.glob(pattern)]
    # Linux / unknown: Arc isn't officially available, but try a sensible default.
    return [Path.home() / ".config" / "Arc" / "StorableSidebar.json"]


def locate_sidebar_file(explicit: Optional[str] = None) -> Path:
    """Resolve the sidebar file, honoring an explicit ``--file`` override.

    Raises FileNotFoundError (with the paths checked) if nothing is found.
    """
    if explicit:
        p = Path(explicit).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"--file path does not exist: {p}")
        return p

    candidates = _candidate_paths()
    for c in candidates:
        if c.is_file():
            return c

    checked = "\n".join(f"  - {c}" for c in candidates) or "  (none for this OS)"
    raise FileNotFoundError(
        "Could not find Arc's StorableSidebar.json. Checked:\n"
        f"{checked}\nPass an explicit path with --file PATH."
    )


def load_sidebar(path: Path) -> dict:
    """Load the sidebar JSON from a temp copy so the original is never touched."""
    tmp_dir = tempfile.mkdtemp(prefix="danfault_arc_")
    tmp_file = Path(tmp_dir) / "StorableSidebar.json"
    try:
        shutil.copy2(path, tmp_file)
        with open(tmp_file, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ──────────────────────────────────────────────────────────────────────────
# Model building
# ──────────────────────────────────────────────────────────────────────────


def _dicts(seq) -> List[dict]:
    """From Arc's marker+dict alternating list, return the dict elements in order."""
    if not isinstance(seq, list):
        return []
    return [x for x in seq if isinstance(x, dict)]


def is_tab(item: dict) -> bool:
    data = item.get("data")
    return isinstance(data, dict) and "tab" in data


def is_folder(item: dict) -> bool:
    data = item.get("data")
    return isinstance(data, dict) and "list" in data


def is_container(item: dict) -> bool:
    data = item.get("data")
    return isinstance(data, dict) and "itemContainer" in data


class Space:
    def __init__(self, title: str, space_id: str, root_ids: List[str]):
        self.title = title
        self.id = space_id
        self.root_ids = root_ids


class Model:
    def __init__(self, items_by_id: Dict[str, dict], spaces: List[Space]):
        self.items_by_id = items_by_id
        self.spaces = spaces


def _resolve_root_ids(space: dict, items_by_id: Dict[str, dict]) -> List[str]:
    """Pull the container ids out of a space's containerIDs / newContainerIDs.

    The list interleaves marker strings ("pinned"/"unpinned") with the actual
    ids; we just keep the entries that exist as items (the itemContainer roots).
    """
    roots: List[str] = []
    for key in ("containerIDs", "newContainerIDs"):
        for entry in space.get(key, []) or []:
            if isinstance(entry, str) and entry in items_by_id and entry not in roots:
                roots.append(entry)
    return roots


def build_model(data: dict) -> Model:
    """Index all items by id and build the ordered list of spaces."""
    sidebar = data.get("sidebar", {})
    containers = sidebar.get("containers", [])
    if not isinstance(containers, list):
        raise ValueError("Unexpected sidebar format: 'containers' is not a list.")

    # Pick the richest data-bearing container (the one with the most items).
    data_containers = [c for c in containers if isinstance(c, dict) and "items" in c]
    if not data_containers:
        raise ValueError("Unexpected sidebar format: no container with 'items' found.")
    container = max(data_containers, key=lambda c: len(c.get("items", [])))

    items_by_id: Dict[str, dict] = {}
    for item in _dicts(container.get("items", [])):
        item_id = item.get("id")
        if item_id:
            items_by_id[item_id] = item

    spaces: List[Space] = []
    for sp in _dicts(container.get("spaces", [])):
        title = sp.get("title") or "(untitled space)"
        spaces.append(Space(title, sp.get("id", ""), _resolve_root_ids(sp, items_by_id)))

    return Model(items_by_id, spaces)


# ──────────────────────────────────────────────────────────────────────────
# Tree walking
# ──────────────────────────────────────────────────────────────────────────


def _tab_title(item: dict) -> str:
    tab = item.get("data", {}).get("tab", {})
    return item.get("title") or tab.get("savedTitle") or tab.get("savedURL") or ""


def walk(item_id: str, items_by_id: Dict[str, dict], skipped: List[int]) -> Optional[dict]:
    """Build a node tree from an item id.

    Returns a node dict: a folder ``{"type":"folder","title","children":[...]}``
    or a tab ``{"type":"tab","title","url"}``. Tabs with no saved URL are skipped
    (counted in ``skipped``). Container roots are transparent — their children are
    returned as folder children.
    """
    item = items_by_id.get(item_id)
    if item is None:
        return None

    if is_tab(item):
        url = item.get("data", {}).get("tab", {}).get("savedURL")
        if not url:
            skipped[0] += 1
            return None
        return {"type": "tab", "title": _tab_title(item), "url": url}

    # Folder or container: recurse into children.
    children: List[dict] = []
    for child_id in item.get("childrenIds", []) or []:
        node = walk(child_id, items_by_id, skipped)
        if node is not None:
            children.append(node)
    title = item.get("title") or ""
    return {"type": "folder", "title": title, "children": children}


def _children_nodes(root_ids: List[str], items_by_id: Dict[str, dict], skipped: List[int]) -> List[dict]:
    """Flatten the children of a set of container roots into a node list."""
    nodes: List[dict] = []
    for rid in root_ids:
        node = walk(rid, items_by_id, skipped)
        if node and node["type"] == "folder":
            nodes.extend(node["children"])
        elif node:
            nodes.append(node)
    return nodes


# ──────────────────────────────────────────────────────────────────────────
# Folder discovery
# ──────────────────────────────────────────────────────────────────────────


def _count_tabs(node: dict) -> int:
    if node["type"] == "tab":
        return 1
    return sum(_count_tabs(c) for c in node["children"])


def find_folders(model: Model) -> List[dict]:
    """Return every folder as ``{space, path, name, node, tab_count}`` in display order."""
    found: List[dict] = []

    def recurse(nodes: List[dict], space_title: str, prefix: List[str]):
        for node in nodes:
            if node["type"] != "folder":
                continue
            name = node["title"] or "(untitled)"
            path = prefix + [name]
            found.append(
                {
                    "space": space_title,
                    "path": path,
                    "name": name,
                    "node": node,
                    "tab_count": _count_tabs(node),
                }
            )
            recurse(node["children"], space_title, path)

    for space in model.spaces:
        skipped = [0]
        top = _children_nodes(space.root_ids, model.items_by_id, skipped)
        recurse(top, space.title, [])
    return found


# ──────────────────────────────────────────────────────────────────────────
# Markdown rendering
# ──────────────────────────────────────────────────────────────────────────


def _escape(text: str) -> str:
    """Escape Markdown-significant characters in a title (emoji preserved)."""
    for ch in ("\\", "`", "[", "]", "|"):
        text = text.replace(ch, "\\" + ch)
    return text


def render_markdown(node: dict, headings: bool = False) -> str:
    """Render a folder node (or a synthetic root) to Markdown.

    Default: nested bullets. With ``headings=True`` the root folder becomes an
    ``##`` heading, subfolders ``###`` (capped at ######), and tabs are flat bullets.
    """
    lines: List[str] = []

    def bullets(children: List[dict], depth: int):
        indent = "  " * depth
        for child in children:
            if child["type"] == "tab":
                lines.append(f"{indent}- [{_escape(child['title'])}]({child['url']})")
            else:
                lines.append(f"{indent}- {_escape(child['title'] or '(untitled)')}")
                bullets(child["children"], depth + 1)

    def headed(folder: dict, level: int):
        hashes = "#" * min(level, 6)
        title = _escape(folder["title"] or "(untitled)")
        lines.append(f"{hashes} {title}")
        lines.append("")
        tabs = [c for c in folder["children"] if c["type"] == "tab"]
        subs = [c for c in folder["children"] if c["type"] == "folder"]
        for tab in tabs:
            lines.append(f"- [{_escape(tab['title'])}]({tab['url']})")
        if tabs:
            lines.append("")
        for sub in subs:
            headed(sub, level + 1)

    if headings:
        headed(node, 1)
    else:
        # Lead with the folder/space name as a header, then its contents as bullets.
        lines.append(f"# {_escape(node['title'] or '(untitled)')}")
        lines.append("")
        bullets(node["children"], 0)

    return "\n".join(lines).rstrip() + "\n"


# ──────────────────────────────────────────────────────────────────────────
# Output helpers
# ──────────────────────────────────────────────────────────────────────────


def _copy_to_clipboard(text: str) -> None:
    """Copy text to the system clipboard (pbcopy/xclip/clip), raising on failure."""
    system = platform.system()
    if system == "Darwin":
        cmd = ["pbcopy"]
    elif system == "Windows":
        cmd = ["clip"]
    else:
        cmd = ["xclip", "-selection", "clipboard"]
    try:
        proc = subprocess.run(cmd, input=text.encode("utf-8"), check=True)
        _ = proc
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise RuntimeError(f"Could not copy to clipboard ({' '.join(cmd)}): {exc}") from None


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────

arc_app = typer.Typer(help="Arc browser utilities.")
tabs_app = typer.Typer(help="Export Arc sidebar folders/spaces to Markdown.")
arc_app.add_typer(tabs_app, name="tabs")


def _load_model(file: Optional[str]) -> Model:
    """Locate + load + build the model, exiting cleanly on known errors."""
    try:
        path = locate_sidebar_file(file)
        data = load_sidebar(path)
        return build_model(data)
    except (FileNotFoundError, ValueError) as exc:
        log.error(str(exc))
        raise typer.Exit(code=1)


@tabs_app.command("list")
def list_tabs(
    space: Optional[str] = typer.Option(
        None, "--space", help="List folders in this space (defaults to the first space)."
    ),
    all_spaces: bool = typer.Option(False, "--all", help="List folders across every space."),
    file: Optional[str] = typer.Option(None, "--file", help="Explicit path to StorableSidebar.json."),
):
    """List the contents of a space as a tree: folders as headings, tabs as bullets.

    Each folder heading is annotated with its recursive tab count, e.g.
    ``## Databricks  [10 tab(s)]``; nesting depth maps to heading level. Without
    flags, lists the first space; ``--space NAME`` picks another. With ``--all``,
    lists every space in parse order — which should match your Arc sidebar order
    (validation step). ``--all`` and ``--space`` are mutually exclusive.
    """
    if all_spaces and space:
        log.error("--all and --space cannot be used together.")
        raise typer.Exit(code=1)

    model = _load_model(file)

    def _print_node(node: dict, level: int):
        hashes = "#" * min(level, 6)
        typer.echo(f"{hashes} {_escape(node['title'] or '(untitled)')}  [{_count_tabs(node)} tab(s)]")
        tabs = [c for c in node["children"] if c["type"] == "tab"]
        subs = [c for c in node["children"] if c["type"] == "folder"]
        for t in tabs:
            typer.echo(f"- [{_escape(t['title'])}]({t['url']})")
        if not node["children"]:
            typer.echo("_(empty)_")
        typer.echo("")
        for s in subs:
            _print_node(s, level + 1)

    if all_spaces:
        typer.echo("Spaces (in parse order — confirm this matches your Arc sidebar):")
        for i, sp in enumerate(model.spaces, start=1):
            typer.echo(f"  {i}. {sp.title}")
        typer.echo("")
        for sp in model.spaces:
            _print_node(_space_root_node(model, sp), 1)
        return

    target = _find_space(model, space, action="listing")
    _print_node(_space_root_node(model, target), 1)


def _find_space(model: Model, space_name: Optional[str], action: str = "backing up") -> Space:
    if space_name:
        matches = [s for s in model.spaces if s.title.lower() == space_name.lower()]
        if not matches:
            names = ", ".join(repr(s.title) for s in model.spaces)
            log.error(f"Space {space_name!r} not found. Available spaces: {names}")
            raise typer.Exit(code=1)
        return matches[0]
    # Default to the first space.
    if not model.spaces:
        log.error("No spaces found in the sidebar data.")
        raise typer.Exit(code=1)
    chosen = model.spaces[0]
    log.warning(
        f"No space given; {action} the first space: {chosen.title!r}. "
        "Run `danfault arc tabs list --all` to confirm this matches your Arc sidebar order."
    )
    return chosen


def _space_root_node(model: Model, space: Space) -> dict:
    """Build a synthetic folder node holding all of a space's top-level items."""
    skipped = [0]
    children = _children_nodes(space.root_ids, model.items_by_id, skipped)
    if skipped[0]:
        log.warning(f"Skipped {skipped[0]} tab(s) with no saved URL.")
    return {"type": "folder", "title": space.title, "children": children}


def _resolve_folder_node(model: Model, folder: str, space_name: Optional[str]) -> dict:
    """Find a folder by name, disambiguating by space; exit cleanly on errors."""
    folders = find_folders(model)
    matches = [f for f in folders if f["name"].lower() == folder.lower()]
    if space_name:
        matches = [f for f in matches if f["space"].lower() == space_name.lower()]

    if not matches:
        all_names = [f["name"] for f in folders]
        close = get_close_matches(folder, all_names, n=5)
        log.error(f"Folder {folder!r} not found.")
        if close:
            log.error("Closest matches: " + ", ".join(repr(c) for c in close))
        raise typer.Exit(code=1)

    if len(matches) > 1:
        log.error(f"Folder {folder!r} is not unique. Candidates (use --space to disambiguate):")
        for m in matches:
            log.error(f"  - {m['space']}: {' / '.join(m['path'])}")
        raise typer.Exit(code=1)

    return matches[0]["node"]


@tabs_app.command("backup")
def backup_tabs(
    folder: Optional[str] = typer.Argument(
        None, help="Folder name to export. Omit to export the whole space."
    ),
    space: Optional[str] = typer.Option(None, "--space", help="Space name (for disambiguation / selection)."),
    out: Optional[str] = typer.Option(None, "--out", help="Write Markdown to this file instead of stdout."),
    clipboard: bool = typer.Option(False, "--clipboard", help="Copy Markdown to the clipboard."),
    headings: bool = typer.Option(False, "--headings", help="Render subfolders as headings, not nested bullets."),
    file: Optional[str] = typer.Option(None, "--file", help="Explicit path to StorableSidebar.json."),
):
    """Export an Arc folder (or a whole space) to a Markdown link list."""
    model = _load_model(file)

    if folder:
        node = _resolve_folder_node(model, folder, space)
    else:
        node = _space_root_node(model, _find_space(model, space))

    if not node["children"]:
        log.warning(f"{node['title']!r} is empty — nothing to export.")

    markdown = render_markdown(node, headings=headings)

    if out:
        Path(out).expanduser().write_text(markdown, encoding="utf-8")
        log.info(f"Wrote {len(markdown.splitlines())} line(s) to {out}")
    if clipboard:
        try:
            _copy_to_clipboard(markdown)
            log.info(f"Copied {len(markdown.splitlines())} line(s) to clipboard.")
        except RuntimeError as exc:
            log.error(str(exc))
            raise typer.Exit(code=1)
    if not out and not clipboard:
        # Default: stdout (pipe-friendly, no log noise on the data stream).
        sys.stdout.write(markdown)


if __name__ == "__main__":
    arc_app()
