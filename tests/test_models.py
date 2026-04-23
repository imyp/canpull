import pytest

from canpull.models import Course, File, Folder, Module, ModuleItem


# --- Raw API response dicts (mirrors real Canvas API shapes) ---

@pytest.fixture
def course_dict():
    return {
        "id": 101,
        "name": "Introduction to Testing",
        "course_code": "TEST101",
        "enrollment_term_id": 5,
    }


@pytest.fixture
def file_dict():
    return {
        "id": 55,
        "display_name": "lecture1.pdf",
        "filename": "lecture1.pdf",
        "content-type": "application/pdf",
        "size": 204800,
        "url": "https://absalon.ku.dk/files/55/download",
        "folder_id": 10,
    }


@pytest.fixture
def module_dict():
    return {"id": 9, "name": "Week 1", "position": 1}


@pytest.fixture
def module_item_dict():
    return {
        "id": 77,
        "title": "Slides",
        "type": "File",
        "content_id": 55,
        "url": None,
    }


@pytest.fixture
def folder_dict():
    return {
        "id": 10,
        "name": "lectures",
        "full_name": "course files/lectures",
        "parent_folder_id": None,
    }



class TestCourseFromApi:
    def test_full_dict(self, course_dict):
        c = Course.from_api(course_dict)
        assert c.id == 101
        assert c.name == "Introduction to Testing"
        assert c.course_code == "TEST101"
        assert c.term == 5

    def test_minimal_dict_no_key_error(self):
        c = Course.from_api({"id": 1})
        assert c.id == 1
        assert c.name == ""
        assert c.course_code == ""
        assert c.term == ""

    def test_missing_name_defaults_to_empty_string(self):
        c = Course.from_api({"id": 2, "course_code": "X"})
        assert c.name == ""

    def test_missing_course_code_defaults_to_empty_string(self):
        c = Course.from_api({"id": 3, "name": "Something"})
        assert c.course_code == ""

    def test_id_is_required(self):
        with pytest.raises(KeyError):
            Course.from_api({"name": "No ID"})


# ---------------------------------------------------------------------------
# File
# ---------------------------------------------------------------------------

class TestFileFromApi:
    def test_full_dict(self, file_dict):
        f = File.from_api(file_dict)
        assert f.id == 55
        assert f.display_name == "lecture1.pdf"
        assert f.filename == "lecture1.pdf"
        assert f.url == "https://absalon.ku.dk/files/55/download"
        assert f.size == 204800
        assert f.folder_id == 10
        assert f.content_type == "application/pdf"

    def test_content_type_hyphen_key(self):
        # Canvas sends "content-type" (hyphenated) — must map to content_type field
        f = File.from_api({"id": 1, "content-type": "application/pdf"})
        assert f.content_type == "application/pdf"

    def test_missing_display_name_falls_back_to_filename(self):
        f = File.from_api({"id": 1, "filename": "slides.pdf"})
        assert f.display_name == "slides.pdf"

    def test_missing_both_names_defaults_to_empty_string(self):
        f = File.from_api({"id": 1})
        assert f.display_name == ""
        assert f.filename == ""

    def test_missing_size_defaults_to_zero(self):
        f = File.from_api({"id": 1})
        assert f.size == 0

    def test_missing_folder_id_defaults_to_zero(self):
        f = File.from_api({"id": 1})
        assert f.folder_id == 0

    def test_missing_url_defaults_to_empty_string(self):
        f = File.from_api({"id": 1})
        assert f.url == ""

    def test_missing_content_type_defaults_to_empty_string(self):
        f = File.from_api({"id": 1})
        assert f.content_type == ""

    def test_id_is_required(self):
        with pytest.raises(KeyError):
            File.from_api({"filename": "x.pdf"})


# ---------------------------------------------------------------------------
# Folder
# ---------------------------------------------------------------------------

class TestFolderFromApi:
    def test_full_dict(self, folder_dict):
        f = Folder.from_api(folder_dict)
        assert f.id == 10
        assert f.name == "lectures"
        assert f.full_name == "course files/lectures"
        assert f.parent_folder_id is None

    def test_with_parent(self):
        f = Folder.from_api({"id": 20, "name": "week1", "full_name": "root/week1",
                              "parent_folder_id": 10})
        assert f.parent_folder_id == 10

    def test_missing_optional_fields(self):
        f = Folder.from_api({"id": 5})
        assert f.name == ""
        assert f.full_name == ""
        assert f.parent_folder_id is None

    def test_id_is_required(self):
        with pytest.raises(KeyError):
            Folder.from_api({"name": "orphan"})


# ---------------------------------------------------------------------------
# Module
# ---------------------------------------------------------------------------

class TestModuleFromApi:
    def test_full_dict(self, module_dict):
        m = Module.from_api(module_dict)
        assert m.id == 9
        assert m.name == "Week 1"
        assert m.position == 1

    def test_missing_name_defaults_to_empty_string(self):
        m = Module.from_api({"id": 1})
        assert m.name == ""

    def test_missing_position_defaults_to_zero(self):
        m = Module.from_api({"id": 1})
        assert m.position == 0

    def test_id_is_required(self):
        with pytest.raises(KeyError):
            Module.from_api({"name": "No ID"})


# ---------------------------------------------------------------------------
# ModuleItem
# ---------------------------------------------------------------------------

class TestModuleItemFromApi:
    def test_full_dict(self, module_item_dict):
        item = ModuleItem.from_api(module_item_dict)
        assert item.id == 77
        assert item.title == "Slides"
        assert item.type == "File"
        assert item.content_id == 55
        assert item.url is None

    def test_non_file_type_has_no_content_id(self):
        item = ModuleItem.from_api({"id": 1, "type": "Assignment", "title": "HW1"})
        assert item.type == "Assignment"
        assert item.content_id is None

    def test_external_url_type(self):
        item = ModuleItem.from_api({"id": 2, "type": "ExternalUrl",
                                    "title": "Link", "url": "https://example.com"})
        assert item.type == "ExternalUrl"
        assert item.url == "https://example.com"
        assert item.content_id is None

    def test_missing_title_defaults_to_empty_string(self):
        item = ModuleItem.from_api({"id": 1})
        assert item.title == ""

    def test_missing_type_defaults_to_empty_string(self):
        item = ModuleItem.from_api({"id": 1})
        assert item.type == ""

    def test_id_is_required(self):
        with pytest.raises(KeyError):
            ModuleItem.from_api({"title": "No ID"})
