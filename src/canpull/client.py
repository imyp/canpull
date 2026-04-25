import http.client
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, NoReturn

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TransferSpeedColumn,
)
from rich.console import Console

from canpull.config import get_base_url, get_token

console = Console()


class CanvasError(Exception):
    pass


class CanvasClient:
    def __init__(self) -> None:
        self._headers = {"Authorization": f"Bearer {get_token()}"}
        self._base_url = get_base_url() + "/api/v1"

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> list[dict]:
        url = self._base_url + endpoint
        results = []
        while url:
            response = self._open(url, params)
            params = None  # only send params on first request
            data = json.loads(response.read().decode())
            if isinstance(data, list):
                results.extend(data)
            else:
                return data
            url = self._next_url(response)
        return results

    def get_one(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = self._base_url + endpoint
        response = self._open(url, params)
        return json.loads(response.read().decode())

    def put(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        url = self._base_url + endpoint
        body = urllib.parse.urlencode(params or {}).encode()
        req = urllib.request.Request(
            url, data=body, headers=self._headers, method="PUT"
        )
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            self._raise_for_status(e)
        return json.loads(response.read().decode())

    def download_file(self, url: str, dest_path: Path, skip_existing: bool = False) -> None:
        if skip_existing and dest_path.exists():
            console.print(f"[dim]Skipping {dest_path.name} (already exists)[/dim]")
            return
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        response = self._open(url)
        total = int(response.headers.get("Content-Length") or 0)
        with Progress(
            TextColumn("[bold blue]{task.fields[filename]}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
        ) as progress:
            task = progress.add_task("", filename=dest_path.name, total=total or None)
            with open(dest_path, "wb") as f:
                while chunk := response.read(8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))

    def _open(
        self, url: str, params: dict[str, Any] | None = None
    ) -> http.client.HTTPResponse:
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self._headers)
        try:
            return urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            self._raise_for_status(e)

    def _raise_for_status(self, error: urllib.error.HTTPError) -> NoReturn:
        try:
            body = json.loads(error.read().decode())
            message = body.get("message") or body.get("errors")
        except Exception:
            message = str(error.reason)
        status = error.code
        if status == 401:
            raise CanvasError("Unauthorized — check your API token.")
        if status == 403:
            raise CanvasError(
                "Permission denied. This course may have the Files tab disabled. "
                "Try 'canpull modules <course_id>' to browse content "
                "via modules instead."
            )
        if status == 404:
            raise CanvasError(f"Not found: {error.url}")
        raise CanvasError(f"HTTP {status}: {message}")

    def _next_url(self, response) -> str | None:
        link_header = response.headers.get("Link") or ""
        match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
        return match.group(1) if match else None

    def resolve_course_id(self, nickname: str) -> int:
        """Resolve a course nickname to a course ID."""
        courses = self.get(
            "/courses", params={"enrollment_state": "active", "per_page": 100}
        )
        ref_lower = nickname.lower()
        matches = [c for c in courses if c.get("name", "").lower() == ref_lower]
        if len(matches) == 1:
            return matches[0]["id"]
        if len(matches) > 1:
            ids = ", ".join(str(c["id"]) for c in matches)
            raise CanvasError(
                f"Ambiguous nickname {nickname!r}: matches course IDs {ids}."
            )
        raise CanvasError(
            f"No active course found with nickname {nickname!r}. "
            "Run 'canpull courses' to list available courses."
        )
