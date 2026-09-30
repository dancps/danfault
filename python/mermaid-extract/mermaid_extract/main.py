from pathlib import Path
from typing import Annotated

import typer

from . import extractor, server

app = typer.Typer(help="Extract mermaid diagrams from a markdown file.")


@app.command()
def extract(
    file: Annotated[Path, typer.Argument(help="Markdown file to parse")],
    serve: Annotated[bool, typer.Option("--server", help="Serve rendered diagrams in the browser")] = False,
    port: Annotated[int, typer.Option(help="Localhost port used with --server")] = 8765,
) -> None:
    if not file.exists():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(1)

    output_dir, diagrams = extractor.extract_and_save(file)

    if not diagrams:
        typer.echo("No mermaid diagrams found.")
        raise typer.Exit(0)

    typer.echo(f"Found {len(diagrams)} diagram(s) → {output_dir}")

    if serve:
        typer.echo(f"Serving at http://localhost:{port}  (Ctrl-C to stop)")
        server.serve(file.stem, port)
