import re


def sanitize_filename(name: str) -> str:
    """Replace characters invalid in Windows filenames with underscores."""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


def title_to_filename(title: str) -> str:
    """Convert a title to a lowercase-dashes .md filename."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug + ".md"
