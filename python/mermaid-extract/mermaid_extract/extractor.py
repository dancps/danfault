from pathlib import Path
import shutil


def extract_and_save(file: Path) -> tuple[Path, list[str]]:
    text = file.read_text(encoding="utf-8")
    diagrams = _parse(text)

    output_dir = Path.home() / ".cache" / "mermaid-extract" / file.stem
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    total = len(diagrams)
    for i, content in enumerate(diagrams, start=1):
        header = f"%% Source: {file.resolve()} (diagram {i} of {total})\n"
        (output_dir / f"{file.stem}_{i}.mmd").write_text(header + content, encoding="utf-8")

    return output_dir, diagrams


def _parse(text: str) -> list[str]:
    diagrams: list[str] = []
    lines = text.splitlines()
    inside = False
    current: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not inside and stripped == "```mermaid":
            inside = True
            current = []
        elif inside and stripped == "```":
            inside = False
            diagrams.append("\n".join(current).strip())
            current = []
        elif inside:
            current.append(line)

    return diagrams
