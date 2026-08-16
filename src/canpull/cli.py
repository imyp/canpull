import typer
from rich.console import Console

from canpull.client import CanvasError, UnauthorizedError
from canpull.commands.announcements import announcement_save_all_cmd, announcements_cmd
from canpull.commands.assignments import assignment_save_all_cmd, assignments_cmd
from canpull.commands.config import config_cmd
from canpull.commands.courses import course_save_cmd, courses_cmd, nickname_course_cmd
from canpull.commands.download import file_download_all_cmd, file_download_cmd
from canpull.commands.files import files_cmd
from canpull.commands.modules import module_list_cmd, module_save_all_cmd
from canpull.commands.pages import (
    page_cmd,
    page_save_all_cmd,
    pages_cmd,
    save_homepage_cmd,
)
from canpull.commands.read import read_cmd
from canpull.commands.whoami import whoami_cmd
from canpull.config import get_token_url, save_token

console = Console()

app = typer.Typer(
    help="canpull - access and download materials from Absalon (Canvas LMS).",
    no_args_is_help=True,
)

# ── course ────────────────────────────────────────────────────────────────────
course_app = typer.Typer(help="Manage courses.", no_args_is_help=True)
app.add_typer(course_app, name="course")
course_app.command("list")(courses_cmd)
course_app.command("nickname")(nickname_course_cmd)
course_app.command("save")(course_save_cmd)

# ── module ────────────────────────────────────────────────────────────────────
module_app = typer.Typer(help="Browse and download course modules.", no_args_is_help=True)
app.add_typer(module_app, name="module")
module_app.command("list")(module_list_cmd)
module_app.command("save-all")(module_save_all_cmd)

# ── page ──────────────────────────────────────────────────────────────────────
page_app = typer.Typer(help="Browse and download course pages.", no_args_is_help=True)
app.add_typer(page_app, name="page")
page_app.command("list")(pages_cmd)
page_app.command("show")(page_cmd)
page_app.command("save-all")(page_save_all_cmd)
page_app.command("save-homepage")(save_homepage_cmd)

# ── file ──────────────────────────────────────────────────────────────────────
file_app = typer.Typer(help="Browse and download course files.", no_args_is_help=True)
app.add_typer(file_app, name="file")
file_app.command("list")(files_cmd)
file_app.command("download")(file_download_cmd)
file_app.command("download-all")(file_download_all_cmd)

# ── announcement ──────────────────────────────────────────────────────────────
announcement_app = typer.Typer(help="Browse and download announcements.", no_args_is_help=True)
app.add_typer(announcement_app, name="announcement")
announcement_app.command("list")(announcements_cmd)
announcement_app.command("save-all")(announcement_save_all_cmd)

# ── assignment ────────────────────────────────────────────────────────────────
assignment_app = typer.Typer(help="Browse course assignments.", no_args_is_help=True)
app.add_typer(assignment_app, name="assignment")
assignment_app.command("list")(assignments_cmd)
assignment_app.command("save-all")(assignment_save_all_cmd)

# ── top-level utilities ───────────────────────────────────────────────────────
app.command("config")(config_cmd)
app.command("read")(read_cmd)
app.command("whoami")(whoami_cmd)


def _prompt_and_save_new_token() -> None:
    token_url = get_token_url()
    console.print("[red]Unauthorized[/red] — your Canvas API token is missing, invalid, or expired.")
    console.print(f"Generate a new one at: [link={token_url}]{token_url}[/link] -> Approved Integrations\n")
    token = typer.prompt("Paste your new Canvas API token", hide_input=True)
    save_token(token)
    console.print("\n[green]Token saved.[/green] Retrying your command...\n")


def main() -> None:
    """Entry point: runs the CLI, turning Canvas errors into readable messages
    instead of raw tracebacks, and offering to save a fresh token on 401s."""
    try:
        app()
    except UnauthorizedError:
        try:
            _prompt_and_save_new_token()
        except (typer.Abort, EOFError):
            console.print("[red]Aborted.[/red] Token was not updated.")
            raise typer.Exit(1)
        try:
            app()
        except CanvasError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    except CanvasError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
