from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from canpull.models import Announcement, Course, File, Module, ModuleItem, Page

console = Console()


def courses_table(courses: list[Course]) -> Table:
    table = Table(title="Enrolled Courses", show_lines=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Code", style="cyan", no_wrap=True)
    table.add_column("Name")
    for c in courses:
        table.add_row(str(c.id), c.course_code, c.name)
    return table


def files_table(files: list[File], downloaded: set[int] | None = None) -> Table:
    table = Table(show_lines=False, show_header=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Size", justify="right", style="dim")
    table.add_column("", no_wrap=True)
    for f in files:
        size = _human_size(f.size)
        is_downloaded = downloaded is not None and f.id in downloaded
        status = "[green]✓[/green]" if is_downloaded else "[dim]-[/dim]"
        table.add_row(str(f.id), f.display_name, size, status)
    return table


def modules_tree(
    modules: list[tuple[Module, list[ModuleItem]]], base_dir: Path | None = None
) -> Tree:
    tree = Tree("[bold]Modules[/bold]")
    for module, items in modules:
        branch = tree.add(f"[cyan]{module.name}[/cyan]")
        for item in items:
            icon = _item_icon(item.type)
            if base_dir is not None and item.type == "Page" and item.page_url:
                is_done = (base_dir / f"{item.page_url}.md").exists()
                status = " [green]✓[/green]" if is_done else " [dim]-[/dim]"
            else:
                status = ""
            branch.add(f"{icon} [dim]{item.id}[/dim]  {item.title}{status}")
    return tree


def pages_table(pages: list[Page], base_dir: Path | None = None) -> Table:
    table = Table(show_lines=False, show_header=True)
    table.add_column("Slug", style="dim", no_wrap=True)
    table.add_column("Title")
    table.add_column("Updated", style="dim", no_wrap=True)
    table.add_column("", no_wrap=True)
    for p in pages:
        updated = p.updated_at[:10] if p.updated_at else ""
        is_downloaded = base_dir is not None and (base_dir / f"{p.url}.md").exists()
        status = "[green]✓[/green]" if is_downloaded else "[dim]-[/dim]"
        table.add_row(p.url, p.title, updated, status)
    return table


def announcements_table(announcements: list[Announcement]) -> Table:
    table = Table(show_lines=False, show_header=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Title")
    table.add_column("Author", style="cyan", no_wrap=True)
    table.add_column("Posted", style="dim", no_wrap=True)
    for a in announcements:
        posted = a.posted_at[:10] if a.posted_at else ""
        table.add_row(str(a.id), a.title, a.author, posted)
    return table


def _human_size(size: int) -> str:
    s: float = size
    for unit in ("B", "KB", "MB", "GB"):
        if s < 1024:
            return f"{s:.0f} {unit}"
        s /= 1024
    return f"{s:.1f} GB"


def _item_icon(item_type: str) -> str:
    return {
        "File": "[blue]F[/blue]",
        "Page": "[green]P[/green]",
        "ExternalUrl": "[yellow]L[/yellow]",
        "Assignment": "[red]A[/red]",
        "Quiz": "[magenta]Q[/magenta]",
    }.get(item_type, " ")
