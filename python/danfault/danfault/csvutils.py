import typer
import pandas as pd

app = typer.Typer()

@app.command()
def to_sheets(file_path: str):
    df = pd.read_csv(file_path)
    df.to_clipboard(index=False)

