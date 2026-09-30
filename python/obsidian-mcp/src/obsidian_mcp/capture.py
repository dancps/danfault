"""
Capture a note into the vault's 00-inbox/ with proper frontmatter,
then trigger an incremental reindex so it's immediately searchable.

Usage:
    obsidian-capture "Some insight" [--vault NAME] --title "OAuth rotation" --domain security --tags oauth tokens
"""
import argparse
import re
from datetime import datetime
from pathlib import Path

from obsidian_mcp import config
from obsidian_mcp.indexer import index_vault


def _yaml_str(value: str) -> str:
    """Quote a scalar so YAML parses it whatever it contains.

    An unquoted title holding a colon (``Recount test: why``) is invalid YAML and breaks every
    consumer of the note's frontmatter.
    """
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def capture(
    text: str,
    title: str | None = None,
    domain: str | None = None,
    tags: list[str] | None = None,
    vault_name: str | None = None,
) -> Path:
    v = config.resolve(vault_name)
    vault = v.path
    if not vault.exists():
        raise ValueError(f"Vault '{v.name}' path does not exist: {vault}")

    inbox = vault / "00-inbox"
    inbox.mkdir(exist_ok=True)

    now = datetime.now()
    date_prefix = now.strftime("%Y-%m-%d")
    display_title = title or now.strftime("%Y-%m-%d %H%M")
    slug = re.sub(r"[^a-z0-9]+", "-", display_title.lower()).strip("-")
    note_path = inbox / f"{date_prefix}-{slug}.md"

    tags_yaml = ", ".join(f'"{t}"' for t in (tags or []))
    content = f"""---
title: {_yaml_str(display_title)}
type: note
domain: {_yaml_str(domain or "")}
tags: [{tags_yaml}]
status: draft
created: {now.strftime("%Y-%m-%d")}
---

{text}
"""
    note_path.write_text(content, encoding="utf-8")
    print(f"Created: {note_path.relative_to(vault)}")

    index_vault(vault, v.db)

    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture a note to the vault inbox")
    parser.add_argument("text", help="Note content")
    parser.add_argument("--title", help="Note title (defaults to timestamp)")
    parser.add_argument("--domain", help="Domain tag, e.g. credit-card, data-platform")
    parser.add_argument("--tags", nargs="*", default=[], help="Additional tags")
    parser.add_argument("--vault", help="Vault name from ~/.config/danfault/vault.yaml (default: default_vault)")
    args = parser.parse_args()

    try:
        capture(
            text=args.text,
            title=args.title,
            domain=args.domain,
            tags=args.tags,
            vault_name=args.vault,
        )
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
