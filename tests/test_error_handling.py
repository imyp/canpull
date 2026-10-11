import pytest

from canpull import cli
from canpull.client import CanvasError, ForbiddenError
from canpull.commands import download


class FilesTabDisabledClient:
    def get_one(self, endpoint, params=None):
        return {"id": 1, "name": "Deep Learning", "course_code": "DL"}

    def get(self, endpoint, params=None):
        raise ForbiddenError("Permission denied.")


def test_download_all_skips_when_files_tab_disabled(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(download, "get_course_dir", lambda course_data: tmp_path)
    download._download_all(FilesTabDisabledClient(), 1)  # type: ignore[arg-type]
    assert "Files tab is disabled" in capsys.readouterr().out


def test_main_exits_cleanly_on_canvas_error(monkeypatch):
    def failing_app():
        raise CanvasError("boom")

    monkeypatch.setattr(cli, "app", failing_app)
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    assert exc_info.value.code == 1
