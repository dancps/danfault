---
name: mermaid-extract
description: Extract mermaid diagrams from a markdown file and optionally render them in the browser via localhost
user-invocable: true
---

# Skill: mermaid-extract

Extract all ` ```mermaid ` blocks from a markdown file. Diagrams are saved as `.mmd` files in `~/.cache/mermaid-extract/<filename>/`. With `--server`, an HTML page using mermaid.js is served at localhost and opened in the browser.

## Usage
```
/mermaid-extract <path/to/file.md>
/mermaid-extract <path/to/file.md> --server
/mermaid-extract <path/to/file.md> --server --port 9000
```

## Instructions

1. Identify the markdown file path from the user's argument. If not provided, ask for it.
2. Run the CLI:
   - Without browser preview: `mermaid-extract <path>`
   - With browser preview: `mermaid-extract <path> --server`
   - Custom port: add `--port <number>`
3. Report back:
   - How many diagrams were found
   - Where the `.mmd` files were saved (`~/.cache/mermaid-extract/<stem>/`)
   - The localhost URL if `--server` was used
4. If no diagrams were found, tell the user and suggest checking the file for ` ```mermaid ` blocks.
