from pathlib import Path

from rich.console import Console

from canpull.client import CanvasClient, CanvasError
from canpull.config import get_course_dir
from canpull.models import File, Folder

console = Console()


def file_download_cmd(course: str, file_id: int):
    """Download a single file by its Canvas file ID."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)
    course_data = client.get_one(f"/courses/{course_id}")
    _download_single(client, file_id, str(get_course_dir(course_data)))


def file_download_all_cmd(course: str):
    """Download all files in a course, preserving folder structure."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)
    _download_all(client, course_id)


def _download_single(client: CanvasClient, file_id: int, dest_dir: str) -> None:
    file_data = client.get_one(f"/files/{file_id}")
    file = File.from_api(file_data)
    dest_path = Path(dest_dir) / file.filename
    console.print(f"Downloading [cyan]{file.display_name}[/cyan] → {dest_path}")
    client.download_file(file.url, dest_path)


def _download_all(client: CanvasClient, course_id: int) -> None:
    course_data = client.get_one(f"/courses/{course_id}")
    base_dir = get_course_dir(course_data)

    folders_data = client.get(f"/courses/{course_id}/folders", params={"per_page": 100})
    folders = {f["id"]: Folder.from_api(f) for f in folders_data}

    files_data = client.get(f"/courses/{course_id}/files", params={"per_page": 100})
    files = [File.from_api(f) for f in files_data]

    for file in files:
        folder = folders.get(file.folder_id)
        rel_path = _folder_relative_path(folder, folders) if folder else Path()
        dest_path = base_dir / "files" / rel_path / file.filename
        console.print(f"[dim]files/{rel_path}/[/dim]{file.display_name}")
        try:
            client.download_file(file.url, dest_path)
        except CanvasError as e:
            console.print(f"[yellow]Skipping {file.display_name}: {e}[/yellow]")

    console.print(f"\n[green]Done.[/green] Files saved to [bold]{base_dir}[/bold]")


def _folder_relative_path(folder: Folder, all_folders: dict[int, Folder]) -> Path:
    parts = []
    current = folder
    seen = set()
    while current and current.parent_folder_id and current.id not in seen:
        seen.add(current.id)
        parts.append(current.name)
        current = all_folders.get(current.parent_folder_id)
    parts.reverse()
    return Path(*parts) if parts else Path()
