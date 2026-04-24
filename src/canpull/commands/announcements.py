import re

from markdownify import markdownify
from rich.console import Console

from canpull.client import CanvasClient
from canpull.commands.pages import _process_page_html, _strip_local_query_params
from canpull.config import get_course_dir
from canpull.models import Announcement
from canpull.utils.display import announcements_table

console = Console()


def _title_to_filename(title: str) -> str:
    """Convert an announcement title to a lowercase-dashes filename."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug + ".md"


def announcements_cmd(course: str):
    """List all announcements in a course."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)
    data = client.get(
        f"/courses/{course_id}/discussion_topics",
        params={"only_announcements": "true", "per_page": 100},
    )
    announcements = [Announcement.from_api(a) for a in data]
    if not announcements:
        console.print("[yellow]No announcements found.[/yellow]")
        return
    console.print(announcements_table(announcements))


def announcement_save_all_cmd(course: str):
    """Download all announcements in a course as Markdown files.

    Each announcement is saved to downloads/<course_code>/ with a filename
    derived from its title (lowercased, spaces replaced with dashes). Linked
    files are downloaded to a shared 'files/' subdirectory.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")
    data = client.get(
        f"/courses/{course_id}/discussion_topics",
        params={"only_announcements": "true", "per_page": 100},
    )
    announcements = [Announcement.from_api(a) for a in data]

    if not announcements:
        console.print("[yellow]No announcements found.[/yellow]")
        return

    course_dir = get_course_dir(course_data)
    dest_dir = course_dir / "announcements"
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_dir = course_dir / "files"
    files_dir.mkdir(exist_ok=True)

    file_id_to_name: dict[int, str] = {}

    for announcement in announcements:
        modified_html, _ = _process_page_html(
            announcement.body, client, files_dir, file_id_to_name, link_prefix="../"
        )
        modified_html = _strip_local_query_params(modified_html)
        md_content = f"# {announcement.title}\n\n{markdownify(modified_html)}"
        filename = _title_to_filename(announcement.title)
        md_path = dest_dir / filename
        md_path.write_text(md_content, encoding="utf-8")
        console.print(f"Saved: [bold]{md_path}[/bold]")

    console.print(
        f"\nDone. Saved [bold]{len(announcements)}[/bold] announcement(s) "
        f"to [bold]{dest_dir}[/bold]"
    )
