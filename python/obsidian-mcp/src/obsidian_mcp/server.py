"""
Obsidian MCP server — read-only retrieval over every indexed vault.

Tools:
    obsidian_list_vaults Vaults registered in the config
    obsidian_search      Hybrid BM25 + semantic search
    obsidian_read_note   Full note content by vault-relative path
    obsidian_list_notes  Filtered note listing
    obsidian_get_context Formatted context block for prompt injection

Every tool except obsidian_list_vaults takes an optional `vault` name; without
it, the config's default_vault is used. Vaults come from
~/.config/danfault/vault.yaml (see obsidian_mcp.config), re-read on each call so
newly registered vaults work without restarting the server.
"""
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from obsidian_mcp import config
from obsidian_mcp.retriever import HybridRetriever

mcp = FastMCP("obsidian")
_retrievers: dict[Path, HybridRetriever] = {}


def _indexed_vault(name: str) -> config.Vault:
    v = config.resolve(name or None)
    if not v.db.exists():
        raise ValueError(
            f"Vault '{v.name}' is not indexed yet. Run: "
            f"uv run --project {config.DATA_DIR.parent} obsidian-index --vault {v.name} --full"
        )
    return v


def get_retriever(v: config.Vault) -> HybridRetriever:
    if v.db not in _retrievers:
        _retrievers[v.db] = HybridRetriever(db_path=str(v.db), vault_path=str(v.path))
    return _retrievers[v.db]


def _safe_path(vault_path: Path, file_path: str) -> Path | None:
    """Resolve path and reject traversal attempts outside the vault."""
    vault = vault_path.resolve()
    target = (vault / file_path).resolve()
    if not target.is_relative_to(vault):
        return None
    return target


@mcp.tool()
def obsidian_list_vaults() -> str:
    """List the Obsidian vaults available to the other tools, marking the default."""
    try:
        vaults = config.list_vaults()
    except ValueError as e:
        return f"Error: {e}"
    if not vaults:
        return "No vaults registered."
    lines = []
    for v in vaults:
        flags = ", ".join(filter(None, ["default" if v.is_default else "", "" if v.db.exists() else "not indexed"]))
        lines.append(f"- **{v.name}** — {v.path}" + (f" ({flags})" if flags else ""))
    return "\n".join(lines)


@mcp.tool()
def obsidian_search(query: str, limit: int = 5, max_tokens: int = 2000, vault: str = "") -> str:
    """Search an Obsidian vault using hybrid BM25 + semantic retrieval.

    Args:
        query: Natural language or keyword query.
        limit: Maximum number of chunks to return (default 5).
        max_tokens: Approximate token budget for returned content (default 2000).
        vault: Vault name from obsidian_list_vaults (default: the configured default vault).
    """
    try:
        v = _indexed_vault(vault)
    except ValueError as e:
        return f"Error: {e}"
    results = get_retriever(v).search(query, limit=limit, max_tokens=max_tokens)
    if not results:
        return "No results found."

    lines = [f"## Vault context ({v.name}): {query}\n"]
    for r in results:
        section = f" › {r['section']}" if r["section"] else ""
        lines.append(f"**{r['file_path']}**{section}")
        lines.append(r["chunk_text"])
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def obsidian_read_note(file_path: str, vault: str = "") -> str:
    """Read the full content of a note by its vault-relative path.

    Args:
        file_path: Vault-relative path, e.g. '03-resources/quark-engine-architecture.md'
        vault: Vault name from obsidian_list_vaults (default: the configured default vault).
    """
    try:
        v = config.resolve(vault or None)
    except ValueError as e:
        return f"Error: {e}"
    target = _safe_path(v.path, file_path)
    if target is None:
        return "Error: path outside vault."
    if not target.exists():
        return f"Note not found: {file_path}"
    return target.read_text(encoding="utf-8")


@mcp.tool()
def obsidian_list_notes(folder: str = "", tag: str = "", limit: int = 20, vault: str = "") -> str:
    """List notes in a vault, optionally filtered by folder or tag.

    Args:
        folder: Vault-relative folder prefix, e.g. '01-projects' (optional).
        tag: Filter by tag value, e.g. 'quark' (optional).
        limit: Max notes to return (default 20).
        vault: Vault name from obsidian_list_vaults (default: the configured default vault).
    """
    try:
        v = _indexed_vault(vault)
    except ValueError as e:
        return f"Error: {e}"
    conn = sqlite3.connect(v.db)
    conn.row_factory = sqlite3.Row

    sql = "SELECT DISTINCT file_path, title, note_type, domain, status FROM chunks WHERE 1=1"
    params: list = []

    if folder:
        sql += " AND file_path LIKE ?"
        params.append(f"{folder.rstrip('/')}/%")
    if tag:
        sql += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')

    sql += f" LIMIT {int(limit)}"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    if not rows:
        return "No notes found."

    lines: list[str] = []
    for r in rows:
        title = r["title"] or Path(r["file_path"]).stem
        meta = " | ".join(filter(None, [r["note_type"], r["domain"], r["status"]]))
        lines.append(f"- **{r['file_path']}** — {title}" + (f" ({meta})" if meta else ""))
    return "\n".join(lines)


@mcp.tool()
def obsidian_get_context(topic: str, max_tokens: int = 1500, vault: str = "") -> str:
    """Get a formatted context block for a topic, for prompt injection.

    Args:
        topic: The topic or question to retrieve context for.
        max_tokens: Approximate token budget (default 1500).
        vault: Vault name from obsidian_list_vaults (default: the configured default vault).
    """
    try:
        v = _indexed_vault(vault)
    except ValueError as e:
        return f"Error: {e}"
    results = get_retriever(v).search(topic, limit=3, max_tokens=max_tokens)
    if not results:
        return ""

    lines = [f"# Vault context ({v.name}): {topic}\n"]
    for r in results:
        section = f" › {r['section']}" if r["section"] else ""
        lines.append(f"Source: `{r['file_path']}`{section}")
        lines.append(r["chunk_text"])
        lines.append("---")
    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
