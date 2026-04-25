from markdownify import markdownify
from rich.console import Console

from canpull.client import CanvasClient
from canpull.commands.pages import _process_page_html, _strip_local_query_params
from canpull.config import get_course_dir
from canpull.models import Assignment
from canpull.utils.display import assignments_table
from canpull.utils.text import title_to_filename

console = Console()


def assignments_cmd(course: str):
    """List all assignments in a course."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)
    data = client.get(
        f"/courses/{course_id}/assignments",
        params={"per_page": 100, "order_by": "due_at"},
    )
    assignments = [Assignment.from_api(a) for a in data]
    if not assignments:
        console.print("[yellow]No assignments found.[/yellow]")
        return
    console.print(assignments_table(assignments))


def assignment_save_all_cmd(course: str, skip_existing: bool = False):
    """Download all assignments in a course as Markdown files.

    Each assignment is saved to downloads/<course_code>/assignments/ with a
    filename derived from its name. Linked files in descriptions are downloaded
    to the shared 'files/' subdirectory.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")
    data = client.get(
        f"/courses/{course_id}/assignments",
        params={"per_page": 100, "order_by": "due_at"},
    )
    assignments = [Assignment.from_api(a) for a in data]

    if not assignments:
        console.print("[yellow]No assignments found.[/yellow]")
        return

    course_dir = get_course_dir(course_data)
    dest_dir = course_dir / "assignments"
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_dir = course_dir / "files"
    files_dir.mkdir(exist_ok=True)

    file_id_to_name: dict[int, str] = {}

    for assignment in assignments:
        due = assignment.due_at[:10] if assignment.due_at else "—"
        points = str(int(assignment.points_possible)) if assignment.points_possible is not None else "—"
        sub_types = ", ".join(assignment.submission_types) if assignment.submission_types else "—"

        metadata = (
            f"- **Due:** {due}\n"
            f"- **Points:** {points}\n"
            f"- **Submission types:** {sub_types}\n"
            f"- **URL:** {assignment.html_url}"
        )

        if assignment.description:
            modified_html, _ = _process_page_html(
                assignment.description, client, files_dir, file_id_to_name,
                link_prefix="../", skip_existing=skip_existing,
            )
            modified_html = _strip_local_query_params(modified_html)
            body = markdownify(modified_html)
            md_content = f"# {assignment.name}\n\n{metadata}\n\n---\n\n{body}"
        else:
            md_content = f"# {assignment.name}\n\n{metadata}\n"

        filename = title_to_filename(assignment.name)
        md_path = dest_dir / filename
        md_path.write_text(md_content, encoding="utf-8")
        console.print(f"Saved: [bold]{md_path}[/bold]")

    console.print(
        f"\nDone. Saved [bold]{len(assignments)}[/bold] assignment(s) "
        f"to [bold]{dest_dir}[/bold]"
    )

