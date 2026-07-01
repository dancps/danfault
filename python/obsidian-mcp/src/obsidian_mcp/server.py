"""
Obsidian MCP server — read-only retrieval over an indexed vault.

Tools:
    obsidian_search      Hybrid BM25 + semantic search
    obsidian_read_note   Full note content by vault-relative path
    obsidian_list_notes  Filtered note listing
    obsidian_get_context Formatted context block for prompt injection

Environment:
    VAULT_PATH   Absolute path to the Obsidian vault
    DB_PATH      Absolute path to the SQLite index (vectors.db)
"""
import os
import sqlite3
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from obsidian_mcp.retriever import HybridRetriever

VAULT_PATH = os.environ.get("VAULT_PATH", "")
DB_PATH = os.environ.get("DB_PATH", "")

mcp = FastMCP("obsidian")
_retriever: HybridRetriever | None = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        if not VAULT_PATH or not DB_PATH:
            raise RuntimeError("VAULT_PATH and DB_PATH must be set")
        _retriever = HybridRetriever(db_path=DB_PATH, vault_path=VAULT_PATH)
    return _retriever


def _safe_path(file_path: str) -> Path | None:
    """Resolve path and reject traversal attempts outside the vault."""
    vault = Path(VAULT_PATH).resolve()
    target = (vault / file_path).resolve()
    if not str(target).startswith(str(vault)):
        return None
    return target


@mcp.tool()
def obsidian_search(query: str, limit: int = 5, max_tokens: int = 2000) -> str:
    """Search the Obsidian vault using hybrid BM25 + semantic retrieval.

    Args:
        query: Natural language or keyword query.
        limit: Maximum number of chunks to return (default 5).
        max_tokens: Approximate token budget for returned content (default 2000).
    """
    results = get_retriever().search(query, limit=limit, max_tokens=max_tokens)
    if not results:
        return "No results found."

    lines = [f"## Vault context: {query}\n"]
    for r in results:
        section = f" › {r['section']}" if r["section"] else ""
        lines.append(f"**{r['file_path']}**{section}")
        lines.append(r["chunk_text"])
        lines.append("")
    return "\n".join(lines)


@mcp.tool()
def obsidian_read_note(file_path: str) -> str:
    """Read the full content of a note by its vault-relative path.

    Args:
        file_path: Vault-relative path, e.g. '03-resources/quark-engine-architecture.md'
    """
    target = _safe_path(file_path)
    if target is None:
        return "Error: path outside vault."
    if not target.exists():
        return f"Note not found: {file_path}"
    return target.read_text(encoding="utf-8")


@mcp.tool()
def obsidian_list_notes(folder: str = "", tag: str = "", limit: int = 20) -> str:
    """List notes in the vault, optionally filtered by folder or tag.

    Args:
        folder: Vault-relative folder prefix, e.g. '01-projects' (optional).
        tag: Filter by tag value, e.g. 'quark' (optional).
        limit: Max notes to return (default 20).
    """
    conn = sqlite3.connect(DB_PATH)
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
def obsidian_get_context(topic: str, max_tokens: int = 1500) -> str:
    """Get a formatted context block for a topic, for prompt injection.

    Args:
        topic: The topic or question to retrieve context for.
        max_tokens: Approximate token budget (default 1500).
    """
    results = get_retriever().search(topic, limit=3, max_tokens=max_tokens)
    if not results:
        return ""

    lines = [f"# Vault context: {topic}\n"]
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
