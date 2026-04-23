import configparser
import os
import stat
from pathlib import Path

import typer

CONFIG_DIR = Path.home() / ".config" / "canpull"
CONFIG_FILE = CONFIG_DIR / "config.ini"

DEFAULT_BASE_URL = "https://absalon.ku.dk"
DEFAULT_DOWNLOADS_DIR = Path.home() / "Downloads" / "canpull"


def get_base_url() -> str:
    url = os.environ.get("CANVAS_URL")
    if url:
        return url.rstrip("/")

    if CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        url = config.get("canvas", "url", fallback=None)
        if url:
            return url.rstrip("/")

    return DEFAULT_BASE_URL


def get_downloads_dir() -> Path:
    path = os.environ.get("CANPULL_DOWNLOADS_DIR")
    if path:
        return Path(path)

    if CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        path = config.get("canvas", "downloads_dir", fallback=None)
        if path:
            return Path(path)

    return DEFAULT_DOWNLOADS_DIR


def get_token() -> str:
    token = os.environ.get("CANVAS_TOKEN")
    if token:
        return token

    if CONFIG_FILE.exists():
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        token = config.get("canvas", "token", fallback=None)
        if token:
            return token

    token = typer.prompt("Enter your Canvas API token", hide_input=True)
    if typer.confirm(f"Save token to {CONFIG_FILE}?"):
        save_token(token)

    return token


def get_course_dir(course_data: dict) -> Path:
    """Return the download directory for a course.

    Uses the course nickname as the folder name if one has been set (Canvas
    signals this by including 'original_name' in the response and putting the
    nickname in 'name'). Otherwise falls back to course_code.
    """
    if "original_name" in course_data:
        folder = course_data["name"]
    else:
        folder = course_data.get("course_code", str(course_data.get("id", "unknown")))
    return get_downloads_dir() / folder.replace("/", "-")


def save_token(token: str) -> None:
    _write_config({"token": token})


def save_config(token: str, url: str, downloads_dir: str) -> None:
    _write_config({"token": token, "url": url, "downloads_dir": downloads_dir})


def _write_config(values: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE)
    if not config.has_section("canvas"):
        config.add_section("canvas")
    for key, value in values.items():
        config.set("canvas", key, value)
    with open(CONFIG_FILE, "w") as f:
        config.write(f)
    CONFIG_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
