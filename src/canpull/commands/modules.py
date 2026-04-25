from urllib.parse import quote

from markdownify import markdownify
from rich.console import Console

from canpull.client import CanvasClient
from canpull.commands.pages import _process_page_html, _strip_local_query_params
from canpull.config import get_course_dir
from canpull.models import File, Module, ModuleItem, Page
from canpull.utils.display import modules_tree

console = Console()


def module_list_cmd(course: str):
    """List all modules and their items in a course."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")

    module_data = client.get(f"/courses/{course_id}/modules", params={"per_page": 100})
    modules = [Module.from_api(m) for m in module_data]

    result = []
    for module in modules:
        item_data = client.get(
            f"/courses/{course_id}/modules/{module.id}/items",
            params={"per_page": 100},
        )
        items = [ModuleItem.from_api(i) for i in item_data]
        result.append((module, items))

    base_dir = get_course_dir(course_data)
    console.print(modules_tree(result, base_dir))


def module_save_all_cmd(course: str):
    """Download all course modules as Markdown files.

    Creates modules.md with a section per module. File items are downloaded to
    a shared 'files/' subdirectory. Page items are downloaded as individual .md
    files. External links are preserved as-is.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")
    course_name = course_data.get("name", str(course_id))

    dest_dir = get_course_dir(course_data)
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_dir = dest_dir / "files"
    files_dir.mkdir(exist_ok=True)

    module_data = client.get(f"/courses/{course_id}/modules", params={"per_page": 100})
    modules = [Module.from_api(m) for m in module_data]

    file_id_to_name: dict[int, str] = {}
    saved_page_slugs: set[str] = set()

    md_lines: list[str] = [f"# {course_name} – Modules\n"]

    for module in modules:
        console.print(f"\n[bold]Module:[/bold] {module.name}")
        item_data = client.get(
            f"/courses/{course_id}/modules/{module.id}/items",
            params={"per_page": 100},
        )
        items = [ModuleItem.from_api(i) for i in item_data]

        md_lines.append(f"\n## {module.name}\n")

        for item in items:
            if item.type == "SubHeader":
                md_lines.append(f"- **{item.title}**")

            elif item.type == "File" and item.content_id is not None:
                if item.content_id not in file_id_to_name:
                    file_resp = client.get_one(f"/files/{item.content_id}")
                    file = File.from_api(file_resp)
                    if not file.url:
                        console.print(f"  [yellow]Skipping {file.display_name}: no download URL available[/yellow]")
                    else:
                        console.print(f"  Downloading [cyan]{file.display_name}[/cyan]")
                        client.download_file(file.url, files_dir / file.filename)
                        file_id_to_name[item.content_id] = file.filename
                filename = file_id_to_name[item.content_id]
                md_lines.append(f"- [{item.title}](files/{quote(filename)})")

            elif item.type == "Page" and item.page_url:
                slug = item.page_url
                if slug not in saved_page_slugs:
                    console.print(f"  Fetching page [bold]{slug}[/bold]")
                    page_resp = client.get_one(f"/courses/{course_id}/pages/{slug}")
                    page = Page.from_api(page_resp)
                    modified_html, _ = _process_page_html(
                        page.body, client, files_dir, file_id_to_name
                    )
                    modified_html = _strip_local_query_params(modified_html)
                    md_content = f"# {page.title}\n\n{markdownify(modified_html)}"
                    md_path = dest_dir / f"{slug}.md"
                    md_path.write_text(md_content, encoding="utf-8")
                    console.print(f"  Saved: [bold]{md_path}[/bold]")
                    saved_page_slugs.add(slug)
                md_lines.append(f"- [{item.title}]({slug}.md)")

            elif item.html_url:
                md_lines.append(f"- [{item.title}]({item.html_url})")

            else:
                md_lines.append(f"- {item.title}")

    modules_md = dest_dir / "modules.md"
    modules_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    console.print(f"\nSaved: [bold]{modules_md}[/bold]")
