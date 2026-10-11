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
    """Download everything for a course: modules, pages, announcements, assignments, and files.

    Runs all five save-all operations in sequence:
      1. module save-all       — module index + linked pages as Markdown + module files
      2. page save-all         — all remaining course pages as Markdown
      3. announcement save-all — all announcements as Markdown
      4. assignment save-all   — all assignments as Markdown
      5. file download-all     — all files preserving folder structure
    """
    from canpull.commands.announcements import announcement_save_all_cmd
    from canpull.commands.assignments import assignment_save_all_cmd
    from canpull.commands.download import file_download_all_cmd
    from canpull.commands.modules import module_save_all_cmd
    from canpull.commands.pages import page_save_all_cmd

    console.rule("[bold]Modules")
    module_save_all_cmd(course, skip_existing=skip_existing)

    console.rule("[bold]Pages")
    page_save_all_cmd(course, skip_existing=skip_existing)

    console.rule("[bold]Announcements")
    announcement_save_all_cmd(course)

    console.rule("[bold]Assignments")
    assignment_save_all_cmd(course, skip_existing=skip_existing)

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


def courses_cmd(
    all_: bool = typer.Option(
        False, "--all", "-a", help="Also show past (completed) courses."
    ),
    past: bool = typer.Option(
        False, "--past", help="Show only past (completed) courses."
    ),
) -> None:
    """List enrolled courses. Shows only active courses unless --all or --past."""
    if all_ and past:
        raise typer.BadParameter("--all and --past cannot be used together.")
    if past:
        states = ["completed"]
    elif all_:
        states = ["active", "completed"]
    else:
        states = ["active"]

    client = CanvasClient()
    courses: list[Course] = []
    statuses: dict[int, str] = {}
    for state in states:
        for c in client.get_courses(state):
            if c["id"] in statuses:
                continue
            courses.append(Course.from_api(c))
            statuses[c["id"]] = "active" if state == "active" else "past"

    if not courses:
        label = "past " if past else "" if all_ else "active "
        console.print(f"[yellow]No {label}courses found.[/yellow]")
        return
    console.print(courses_table(courses, statuses if len(states) > 1 else None))
