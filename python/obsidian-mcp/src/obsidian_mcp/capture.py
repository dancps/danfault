"""
Capture a note into the vault's 00-inbox/ with proper frontmatter,
then trigger an incremental reindex so it's immediately searchable.

Usage:
    obsidian-capture "Some insight" --title "OAuth rotation" --domain security --tags oauth tokens
"""
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def capture(
    text: str,
    title: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    vault_path: str | None = None,
    db_path: str | None = None,
) -> Path:
    vault = Path(vault_path or os.environ.get("VAULT_PATH", ""))
    if not vault or not vault.exists():
        raise ValueError("VAULT_PATH is not set or does not exist")

    inbox = vault / "00-inbox"
    inbox.mkdir(exist_ok=True)

    now = datetime.now()
    date_prefix = now.strftime("%Y-%m-%d")
    display_title = title or now.strftime("%Y-%m-%d %H%M")
    slug = re.sub(r"[^a-z0-9]+", "-", display_title.lower()).strip("-")
    note_path = inbox / f"{date_prefix}-{slug}.md"

    tags_yaml = ", ".join(f'"{t}"' for t in (tags or []))
    content = f"""---
title: {display_title}
type: note
domain: {domain or ""}
tags: [{tags_yaml}]
status: draft
created: {now.strftime("%Y-%m-%d")}
---

{text}
"""
    note_path.write_text(content, encoding="utf-8")
    print(f"Created: {note_path.relative_to(vault)}")

    db = db_path or os.environ.get("DB_PATH", "")
    if db:
        result = subprocess.run(
            ["uv", "run", "obsidian-index", "--vault", str(vault), "--db", db],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Warning: reindex failed — {result.stderr.strip()}", file=sys.stderr)
        else:
            print(result.stdout.strip())

    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a note to the vault inbox")
    parser.add_argument("text", help="Note content")
    parser.add_argument("--title", help="Note title (defaults to timestamp)")
    parser.add_argument("--domain", help="Domain tag, e.g. credit-card, data-platform")
    parser.add_argument("--tags", nargs="*", default=[], help="Additional tags")
    parser.add_argument("--vault", default=os.environ.get("VAULT_PATH"), help="Vault path")
    parser.add_argument("--db", default=os.environ.get("DB_PATH"), help="SQLite DB path")
    args = parser.parse_args()

    capture(
        text=args.text,
        title=args.title,
        domain=args.domain,
        tags=args.tags,
        vault_path=args.vault,
        db_path=args.db,
    )


if __name__ == "__main__":
    main()
