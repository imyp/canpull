from dataclasses import dataclass, field
from urllib.parse import unquote_plus


@dataclass
class Course:
    id: int
    name: str
    course_code: str
    term: str

    @classmethod
    def from_api(cls, data: dict) -> "Course":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            course_code=data.get("course_code", ""),
            term=data.get("enrollment_term_id", ""),
        )


@dataclass
class File:
    id: int
    display_name: str
    filename: str
    url: str
    size: int
    folder_id: int
    content_type: str

    @classmethod
    def from_api(cls, data: dict) -> "File":
        return cls(
            id=data["id"],
            display_name=data.get("display_name", data.get("filename", "")),
            filename=unquote_plus(data.get("filename", "")),  
            url=data.get("url", ""),
            size=data.get("size", 0),
            folder_id=data.get("folder_id", 0),
            content_type=data.get("content-type", ""),
        )


@dataclass
class Folder:
    id: int
    name: str
    full_name: str
    parent_folder_id: int | None

    @classmethod
    def from_api(cls, data: dict) -> "Folder":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            full_name=data.get("full_name", ""),
            parent_folder_id=data.get("parent_folder_id"),
        )


@dataclass
class Module:
    id: int
    name: str
    position: int

    @classmethod
    def from_api(cls, data: dict) -> "Module":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            position=data.get("position", 0),
        )


@dataclass
class Page:
    page_id: int
    url: str  # slug used in API calls, e.g. "week-1-introduction"
    title: str
    updated_at: str
    body: str = field(default="")  # only populated when fetching a single page

    @classmethod
    def from_api(cls, data: dict) -> "Page":
        return cls(
            page_id=data.get("page_id", 0),
            url=data.get("url", ""),
            title=data.get("title", ""),
            updated_at=data.get("updated_at", ""),
            body=data.get("body") or "",
        )


@dataclass
class Announcement:
    id: int
    title: str
    author: str
    posted_at: str
    body: str = field(default="")  # only populated when fetching a single announcement

    @classmethod
    def from_api(cls, data: dict) -> "Announcement":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            author=data.get("author", {}).get("display_name", ""),
            posted_at=data.get("posted_at", ""),
            body=data.get("message") or "",
        )


@dataclass
class ModuleItem:
    id: int
    title: str
    type: str
    content_id: int | None
    url: str | None  # Canvas API endpoint URL
    html_url: str | None  # browser-navigable URL
    page_url: str | None  # slug for Page-type items, e.g. "week-1-introduction"

    @classmethod
    def from_api(cls, data: dict) -> "ModuleItem":
        return cls(
            id=data["id"],
            title=data.get("title", ""),
            type=data.get("type", ""),
            content_id=data.get("content_id"),
            url=data.get("url"),
            html_url=data.get("html_url"),
            page_url=data.get("page_url"),
        )


@dataclass
class Assignment:
    id: int
    name: str
    due_at: str
    points_possible: float | None
    submission_types: list[str]
    html_url: str

    @classmethod
    def from_api(cls, data: dict) -> "Assignment":
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            due_at=data.get("due_at") or "",
            points_possible=data.get("points_possible"),
            submission_types=data.get("submission_types") or [],
            html_url=data.get("html_url") or "",
        )
