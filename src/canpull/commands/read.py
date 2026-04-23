import tempfile
from pathlib import Path

import typer
from rich.console import Console

from canpull.client import CanvasClient
from canpull.utils.pdf import extract_text

console = Console()


def read_cmd(
    target: str,
    file_id: int | None = typer.Option(
        None, "--file-id", help="File ID to download and read from a course."
    ),
):
    """Extract text from a PDF.

    TARGET is either a local file path or a course ID (when used with --file-id).
    """
    if file_id:
        client = CanvasClient()
        file_data = client.get_one(f"/files/{file_id}")
        url = file_data.get("url", "")
        filename = file_data.get("filename", "file.pdf")
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / filename
            client.download_file(url, dest)
            text = extract_text(dest)
    else:
        path = Path(target)
        if not path.exists():
            typer.echo(f"Error: File not found: {path}", err=True)
        raise typer.Exit(1)
        text = extract_text(path)

    typer.echo(text)
