import typer

from canpull.commands.announcements import announcement_save_all_cmd, announcements_cmd
from canpull.commands.assignments import assignments_cmd
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

main = typer.Typer(
    help="canpull - access and download materials from Absalon (Canvas LMS).",
    no_args_is_help=True,
)

# ── course ────────────────────────────────────────────────────────────────────
course_app = typer.Typer(help="Manage courses.", no_args_is_help=True)
main.add_typer(course_app, name="course")
course_app.command("list")(courses_cmd)
course_app.command("nickname")(nickname_course_cmd)
course_app.command("save")(course_save_cmd)

# ── module ────────────────────────────────────────────────────────────────────
module_app = typer.Typer(help="Browse and download course modules.", no_args_is_help=True)
main.add_typer(module_app, name="module")
module_app.command("list")(module_list_cmd)
module_app.command("save-all")(module_save_all_cmd)

# ── page ──────────────────────────────────────────────────────────────────────
page_app = typer.Typer(help="Browse and download course pages.", no_args_is_help=True)
main.add_typer(page_app, name="page")
page_app.command("list")(pages_cmd)
page_app.command("show")(page_cmd)
page_app.command("save-all")(page_save_all_cmd)
page_app.command("save-homepage")(save_homepage_cmd)

# ── file ──────────────────────────────────────────────────────────────────────
file_app = typer.Typer(help="Browse and download course files.", no_args_is_help=True)
main.add_typer(file_app, name="file")
file_app.command("list")(files_cmd)
file_app.command("download")(file_download_cmd)
file_app.command("download-all")(file_download_all_cmd)

# ── announcement ──────────────────────────────────────────────────────────────
announcement_app = typer.Typer(help="Browse and download announcements.", no_args_is_help=True)
main.add_typer(announcement_app, name="announcement")
announcement_app.command("list")(announcements_cmd)
announcement_app.command("save-all")(announcement_save_all_cmd)

# ── assignment ────────────────────────────────────────────────────────────────
assignment_app = typer.Typer(help="Browse course assignments.", no_args_is_help=True)
main.add_typer(assignment_app, name="assignment")
assignment_app.command("list")(assignments_cmd)

# ── top-level utilities ───────────────────────────────────────────────────────
main.command("config")(config_cmd)
main.command("read")(read_cmd)
