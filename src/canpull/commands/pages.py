import html
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from markdownify import markdownify
from rich.console import Console
from rich.text import Text

from canpull.client import CanvasClient, CanvasError
from canpull.config import get_base_url, get_course_dir
from canpull.models import File, Page
from canpull.utils.display import pages_table

# Matches Canvas file URLs in both relative and absolute forms, e.g.:
#   /courses/123/files/456/download
#   /files/456/preview
#   https://absalon.ku.dk/courses/123/files/456
_CANVAS_FILE_RE = re.compile(
    r"((?:https?://[^/\"'<>\s]+)?/(?:courses/\d+/)?files/(\d+)(?:/[^\s\"'<>]*)?"
    r")"
)

# Matches Canvas page links in both relative and absolute forms, e.g.:
#   /courses/123/pages/some-slug
#   https://absalon.ku.dk/courses/123/pages/some-slug
#   /courses/123/wiki/some-slug  (legacy Canvas URL format)
_CANVAS_PAGE_RE = re.compile(
    r"((?:https?://[^/\"'<>\s]+)?/courses/(\d+)/(?:pages|wiki)/([^\"'\s<>?#/]+))"
)

console = Console()

_BLOCK_TAGS = {
    "p",
    "div",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "tr",
    "br",
    "hr",
    "blockquote",
    "pre",
}

_HEADING_STYLE = {
    "h1": "bold underline",
    "h2": "bold",
    "h3": "bold dim",
    "h4": "dim",
    "h5": "dim",
    "h6": "dim",
}


class _RichTextExtractor(HTMLParser):
    """Convert HTML to a rich.Text object, preserving links as clickable hyperlinks."""

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self._base_url = base_url.rstrip("/")
        self._text = Text()
        self._link_href: str | None = None
        self._heading_style: str = ""
        # Pending newlines: buffer them so we never emit trailing blank lines
        self._pending_newlines: int = 0

    def _flush_newlines(self) -> None:
        if self._pending_newlines:
            self._text.append("\n" * self._pending_newlines)
            self._pending_newlines = 0

    def _queue_newlines(self, n: int) -> None:
        # Keep only the maximum of what's already queued — avoids triple+ blank lines
        self._pending_newlines = max(self._pending_newlines, n)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in _BLOCK_TAGS:
            self._queue_newlines(1)
        if tag == "li":
            self._flush_newlines()
            self._text.append("• ")
            self._pending_newlines = 0
        if tag in _HEADING_STYLE:
            self._queue_newlines(2)
            self._heading_style = _HEADING_STYLE[tag]
        if tag == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href", "")
            if href and href.startswith("/"):
                href = self._base_url + href
            self._link_href = href or None

    def handle_endtag(self, tag: str) -> None:
        if tag in _HEADING_STYLE:
            self._heading_style = ""
            self._queue_newlines(2)
        if tag == "a":
            self._link_href = None

    def handle_data(self, data: str) -> None:
        stripped = data.strip()
        if not stripped:
            return
        self._flush_newlines()
        style = self._heading_style
        if self._link_href:
            style = (style + " " if style else "") + f"link {self._link_href}"
        self._text.append(data, style=style or None)

    def handle_entityref(self, name: str) -> None:
        self.handle_data(html.unescape(f"&{name};"))

    def handle_charref(self, name: str) -> None:
        self.handle_data(html.unescape(f"&#{name};"))

    def get_text(self) -> Text:
        return self._text


def _html_to_rich(body: str, base_url: str) -> Text:
    extractor = _RichTextExtractor(base_url)
    extractor.feed(body)
    return extractor.get_text()


def pages_cmd(course: str):
    """List all pages in a course."""
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")

    try:
        data = client.get(f"/courses/{course_id}/pages", params={"per_page": 100})
    except CanvasError as e:
        if "Not found" in str(e):
            console.print("[yellow]Pages are not enabled for this course.[/yellow]")
            return
        raise
    pages = [Page.from_api(p) for p in data]
    if not pages:
        console.print("[yellow]No pages found.[/yellow]")
        return

    base_dir = get_course_dir(course_data)
    console.print(pages_table(pages, base_dir))


_EXTERNAL_SCHEMES = ("http://", "https://", "ftp://", "mailto://", "//")


def _strip_local_query_params(html_body: str) -> str:
    """Strip query strings and fragments from local (non-external) href/src attributes.

    Canvas injects verifier tokens into file URLs (e.g. 'file.pdf?verifier=ABC&wrap=1').
    After the Canvas URL has been rewritten to a local filename these tokens are
    meaningless and break file resolution in markdown readers.
    """
    soup = BeautifulSoup(html_body, "html.parser")
    for attr in ("href", "src"):
        for tag in soup.find_all(attrs={attr: True}):
            val = tag[attr]
            if not isinstance(val, str):
                continue
            if not val.startswith(_EXTERNAL_SCHEMES):
                clean = val.split("?")[0].split("#")[0]
                if clean != val:
                    tag[attr] = clean
    return str(soup)


def _process_page_html(
    html_body: str,
    client: CanvasClient,
    files_dir: Path,
    file_id_to_name: dict[int, str],
    link_prefix: str = "",
) -> tuple[str, list[tuple[int, str]]]:
    """Download file attachments and rewrite URLs for multi-page downloads.

    Files are saved to files_dir and rewritten to '<link_prefix>files/<filename>'.
    Canvas page links are rewritten to '<link_prefix><slug>.md'.
    link_prefix should be a relative path (e.g. '../') when the output file lives
    in a subdirectory of the course root.
    file_id_to_name is mutated in-place and shared across all pages to deduplicate.

    Returns:
        modified HTML, list of (course_id, page_slug) for discovered linked pages.
    """
    url_to_name: dict[str, str] = {}

    for match in _CANVAS_FILE_RE.finditer(html_body):
        original_url = match.group(1)
        file_id = int(match.group(2))

        if original_url in url_to_name:
            continue

        if file_id not in file_id_to_name:
            try:
                file_data = client.get_one(f"/files/{file_id}")
                file = File.from_api(file_data)
                if not file.url:
                    console.print(f"[yellow]Skipping file {file_id}: no download URL available[/yellow]")
                    continue
                console.print(f"Downloading [cyan]{file.display_name}[/cyan]")
                client.download_file(file.url, files_dir / file.filename)
                file_id_to_name[file_id] = file.filename
            except CanvasError as e:
                console.print(f"[yellow]Skipping file {file_id}: {e}[/yellow]")
                continue

        url_to_name[original_url] = f"{link_prefix}files/{quote(file_id_to_name[file_id])}"

    for original_url in sorted(url_to_name, key=len, reverse=True):
        html_body = html_body.replace(original_url, url_to_name[original_url])

    discovered_pages: list[tuple[int, str]] = []
    page_url_to_local: dict[str, str] = {}

    for match in _CANVAS_PAGE_RE.finditer(html_body):
        original_url = match.group(1)
        course_id = int(match.group(2))
        slug = match.group(3)

        if original_url not in page_url_to_local:
            page_url_to_local[original_url] = f"{link_prefix}{slug}.md"
            discovered_pages.append((course_id, slug))

    for original_url in sorted(page_url_to_local, key=len, reverse=True):
        html_body = html_body.replace(original_url, page_url_to_local[original_url])

    return html_body, discovered_pages


def page_save_all_cmd(course: str):
    """Download all pages in a course as Markdown files.

    Each page is saved as <slug>.md in the course directory. File attachments
    linked within pages are downloaded once to a shared 'files/' subdirectory.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")
    dest_dir = get_course_dir(course_data)
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_dir = dest_dir / "files"
    files_dir.mkdir(exist_ok=True)

    try:
        pages_data = client.get(f"/courses/{course_id}/pages", params={"per_page": 100})
    except CanvasError as e:
        if "Not found" in str(e):
            console.print("[yellow]Pages are not enabled for this course.[/yellow]")
            return
        raise
    slugs = [p["url"] for p in pages_data]

    if not slugs:
        console.print("[yellow]No pages found.[/yellow]")
        return

    file_id_to_name: dict[int, str] = {}

    for slug in slugs:
        console.print(f"Fetching page [bold]{slug}[/bold]")
        page_data = client.get_one(f"/courses/{course_id}/pages/{slug}")
        page = Page.from_api(page_data)
        modified_html, _ = _process_page_html(
            page.body, client, files_dir, file_id_to_name
        )
        modified_html = _strip_local_query_params(modified_html)
        md_content = f"# {page.title}\n\n{markdownify(modified_html)}"
        md_path = dest_dir / f"{slug}.md"
        md_path.write_text(md_content, encoding="utf-8")
        console.print(f"Saved: [bold]{md_path}[/bold]")

    console.print(
        f"\nDone. Saved [bold]{len(slugs)}[/bold] page(s) to [bold]{dest_dir}[/bold]"
    )


def save_homepage_cmd(course: str):
    """Download the course homepage as a Markdown file.

    Saved to downloads/<course_code>/<slug>.md with linked files in files/.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)

    course_data = client.get_one(f"/courses/{course_id}")

    page_data = client.get_one(f"/courses/{course_id}/front_page")
    page = Page.from_api(page_data)

    dest_dir = get_course_dir(course_data)
    dest_dir.mkdir(parents=True, exist_ok=True)
    files_dir = dest_dir / "files"
    files_dir.mkdir(exist_ok=True)

    file_id_to_name: dict[int, str] = {}
    modified_html, _ = _process_page_html(page.body, client, files_dir, file_id_to_name)
    modified_html = _strip_local_query_params(modified_html)
    md_content = f"# {page.title}\n\n{markdownify(modified_html)}"

    md_path = dest_dir / f"{page.url}.md"
    md_path.write_text(md_content, encoding="utf-8")
    console.print(f"Saved: [bold]{md_path}[/bold]")


def page_cmd(course: str, page_url: str):
    """Show the content of a single page.

    PAGE_URL is the slug shown in the 'canpull pages' listing
    (e.g. week-1-introduction).
    Links in the page are preserved as clickable hyperlinks in supported terminals.
    """
    client = CanvasClient()
    course_id = client.resolve_course_id(course)
    data = client.get_one(f"/courses/{course_id}/pages/{page_url}")
    page = Page.from_api(data)
    console.print(f"[bold]{page.title}[/bold]\n")
    console.print(_html_to_rich(page.body, get_base_url()))
