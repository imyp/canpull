import typer
from rich.console import Console

from canpull.client import CanvasClient
from canpull.models import Course
from canpull.utils.display import courses_table

console = Console()


def course_save_cmd(
    course: str,
    skip_existing: bool = typer.Option(False, "--skip-existing", help="Skip files that already exist locally."),
) -> None:
    """Download everything for a course: modules, pages, announcements, and files.

    Runs all four save-all operations in sequence:
      1. module save-all  — module index + linked pages as Markdown + module files
      2. page save-all    — all remaining course pages as Markdown
      3. announcement save-all — all announcements as Markdown
      4. file download-all    — all files preserving folder structure
    """
    from canpull.commands.announcements import announcement_save_all_cmd
    from canpull.commands.download import file_download_all_cmd
    from canpull.commands.modules import module_save_all_cmd
    from canpull.commands.pages import page_save_all_cmd

    console.rule("[bold]Modules")
    module_save_all_cmd(course, skip_existing=skip_existing)

    console.rule("[bold]Pages")
    page_save_all_cmd(course, skip_existing=skip_existing)

    console.rule("[bold]Announcements")
    announcement_save_all_cmd(course)

    console.rule("[bold]Files")
    file_download_all_cmd(course, skip_existing=skip_existing)

    console.rule()
    console.print(f"[green bold]Done.[/green bold] All content saved for [bold]{course}[/bold].")


def nickname_course_cmd(
    course_id: int,
    name: str = typer.Argument(..., help="Nickname to show for the course in Canvas."),
) -> None:
    """Set a personal nickname for a course in Canvas.

    The nickname is visible only to you and appears everywhere in the Canvas
    UI instead of the original course name. The original name is preserved
    under 'original_name' in the API.
    """
    client = CanvasClient()
    result = client.put(
        f"/users/self/course_nicknames/{course_id}",
        params={"nickname": name},
    )
    applied = result.get("nickname", name)
    console.print(
        f"Nickname set: [dim]{course_id}[/dim] → [bold]{applied}[/bold]"
    )


def courses_cmd():
    """List all active enrolled courses."""
    client = CanvasClient()
    data = client.get(
        "/courses", params={"enrollment_state": "active", "per_page": 100}
    )
    courses = [Course.from_api(c) for c in data]
    if not courses:
        console.print("[yellow]No active courses found.[/yellow]")
        return
    console.print(courses_table(courses))
