from pathlib import Path

from rich.console import Console

from canpull.client import CanvasClient
from canpull.commands.download import _folder_relative_path
from canpull.config import get_course_dir
from canpull.models import File, Folder
from canpull.utils.display import files_table

console = Console()


def _is_downloaded(f: File, base_dir: Path, folders: dict[int, Folder]) -> bool:
    rel_path = (
        _folder_relative_path(folders[f.folder_id], folders)
        if f.folder_id in folders
        else Path()
    )
    if (base_dir / rel_path / f.filename).exists():
        return True
    # Also check the flat files/ subdir used by save-modules
    if (base_dir / "files" / f.filename).exists():
        return True
    return False


def files_cmd(course: str):
    """List all files in a course."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")

    folders_data = client.get(f"/courses/{course_id}/folders", params={"per_page": 100})
    folders = {f["id"]: Folder.from_api(f) for f in folders_data}

    data = client.get(f"/courses/{course_id}/files", params={"per_page": 100})
    files = [File.from_api(f) for f in data]

    if not files:
        console.print("[yellow]No files found.[/yellow]")
        return

    base_dir = get_course_dir(course_data)
    downloaded = {
        f.id
        for f in files
        if _is_downloaded(f, base_dir, folders)
    }

    console.print(files_table(files, downloaded))



