"""
Index an Obsidian vault into SQLite with BM25 tokens and embeddings.

Usage:
    VAULT_PATH=... DB_PATH=... obsidian-index [--full]
"""
import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

import frontmatter
import numpy as np
import pathspec
from model2vec import StaticModel

SCHEMA = """
CREATE TABLE IF NOT EXISTS chunks (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path        TEXT    NOT NULL,
    section_heading  TEXT    NOT NULL DEFAULT '',
    chunk_text       TEXT    NOT NULL,
    tokens           TEXT    NOT NULL,
    embedding        BLOB    NOT NULL,
    file_mtime       REAL    NOT NULL,
    title            TEXT,
    note_type        TEXT,
    domain           TEXT,
    tags             TEXT,
    status           TEXT,
    UNIQUE(file_path, section_heading)
);
CREATE TABLE IF NOT EXISTS index_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


def load_indexignore(vault_path: Path) -> pathspec.PathSpec:
    ignore_file = vault_path / ".indexignore"
    patterns: list[str] = [".obsidian/", "*.db"]
    if ignore_file.exists():
        for line in ignore_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def split_chunks(text: str) -> list[tuple[str, str]]:
    """Split note body at H2 boundaries. Returns (heading, body) pairs."""
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)
    parts = re.split(r"^(## .+)$", body, flags=re.MULTILINE)

    chunks: list[tuple[str, str]] = []
    if parts[0].strip():
        chunks.append(("", parts[0].strip()))
    for i in range(1, len(parts), 2):
        heading = parts[i].lstrip("#").strip()
        body_part = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if heading or body_part:
            chunks.append((heading, body_part))

    return chunks or [("", body.strip())]


def tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def index_vault(vault_path: Path, db_path: Path, full: bool = False) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print("Loading embedding model...")
    model = StaticModel.from_pretrained("minishlab/potion-base-8M")
    spec = load_indexignore(vault_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()

    if full:
        conn.execute("DELETE FROM chunks")
        conn.commit()
        print("Full reindex — cleared existing chunks.")

    md_files = sorted(vault_path.rglob("*.md"))
    indexed = skipped = 0

    for md_file in md_files:
        rel = md_file.relative_to(vault_path)
        if spec.match_file(str(rel)):
            continue

        mtime = md_file.stat().st_mtime

        if not full:
            row = conn.execute(
                "SELECT file_mtime FROM chunks WHERE file_path = ? LIMIT 1",
                (str(rel),),
            ).fetchone()
            if row and abs(row["file_mtime"] - mtime) < 0.01:
                skipped += 1
                continue

        text = md_file.read_text(encoding="utf-8", errors="replace")
        post = frontmatter.loads(text)
        fm = post.metadata

        conn.execute("DELETE FROM chunks WHERE file_path = ?", (str(rel),))

        for heading, body in split_chunks(text):
            chunk_text = (f"## {heading}\n{body}" if heading else body).strip()
            if not chunk_text:
                continue

            embedding = model.encode([chunk_text])[0].astype(np.float32)
            tokens = tokenize(chunk_text)

            conn.execute(
                """INSERT OR REPLACE INTO chunks
                   (file_path, section_heading, chunk_text, tokens, embedding,
                    file_mtime, title, note_type, domain, tags, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(rel),
                    heading,
                    chunk_text,
                    json.dumps(tokens),
                    embedding.tobytes(),
                    mtime,
                    fm.get("title"),
                    fm.get("type"),
                    fm.get("domain"),
                    json.dumps(fm.get("tags", [])),
                    fm.get("status"),
                ),
            )
            indexed += 1

        conn.commit()

    print(f"Done. {indexed} chunks indexed, {skipped} files unchanged.")
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Index Obsidian vault into SQLite")
    parser.add_argument("--full", action="store_true", help="Full reindex (ignore mtimes)")
    parser.add_argument("--vault", default=os.environ.get("VAULT_PATH"), help="Vault path")
    parser.add_argument("--db", default=os.environ.get("DB_PATH"), help="SQLite DB path")
    args = parser.parse_args()

    if not args.vault:
        parser.error("VAULT_PATH env var or --vault required")
    if not args.db:
        parser.error("DB_PATH env var or --db required")

    index_vault(Path(args.vault), Path(args.db), full=args.full)


if __name__ == "__main__":
    main()
