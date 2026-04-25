from rich.console import Console

from canpull.client import CanvasClient
from canpull.models import Assignment
from canpull.utils.display import assignments_table

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
