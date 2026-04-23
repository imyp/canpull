# canpull

CLI tool for downloading course material from Absalon (Canvas LMS) to your local filesystem.

## Setup

```
uv sync --all-extras
uv run canpull --help
```

Configure your Canvas API token and instance URL:

```
uv run canpull config
```

Or set environment variables:

```
CANVAS_TOKEN=<your-token>
CANVAS_URL=https://absalon.ku.dk        # default
CANPULL_DOWNLOADS_DIR=~/Downloads/canpull  # default
```

## Commands

### `canpull course`

| Command | Description |
|---|---|
| `canpull course list` | List enrolled courses |
| `canpull course nickname <course> <name>` | Set a short nickname for a course |
| `canpull course save <course>` | Download all content for a course (modules, pages, announcements, files) |

### `canpull module`

| Command | Description |
|---|---|
| `canpull module list <course>` | List modules and their items |
| `canpull module save-all <course>` | Save all module pages as Markdown and download module files |

### `canpull page`

| Command | Description |
|---|---|
| `canpull page list <course>` | List all pages |
| `canpull page show <course> <page>` | Print a page to the terminal |
| `canpull page save-all <course>` | Save all pages as Markdown |
| `canpull page save-homepage <course>` | Save the course homepage as Markdown |

### `canpull file`

| Command | Description |
|---|---|
| `canpull file list <course>` | List all files |
| `canpull file download <course> <file-id>` | Download a single file by ID |
| `canpull file download-all <course>` | Download all files, preserving folder structure |

### `canpull announcement`

| Command | Description |
|---|---|
| `canpull announcement list <course>` | List announcements |
| `canpull announcement save-all <course>` | Save all announcements as Markdown |

### Top-level

| Command | Description |
|---|---|
| `canpull config` | Set or update configuration (token, URL, downloads directory) |
| `canpull read <file>` | Print a downloaded Markdown file to the terminal |

## Course identifiers

Most commands accept a `<course>` argument. You can use:

- A nickname you set with `canpull course nickname` (e.g. `vt`)
- A Canvas course code (e.g. `NDAB21024E`)
- A numeric Canvas course ID (e.g. `12345`)

## Output layout

All content is saved under the configured downloads directory (default `~/Downloads/canpull`), organised by course:

```
~/Downloads/canpull/
└── <course-folder>/
    ├── modules.md              # module index
    ├── <page-slug>.md          # pages and module pages
    ├── announcements/
    │   └── <title-slug>.md
    └── files/
        ├── <file>              # root-level course files
        └── <subfolder>/
            └── <file>
```

## Notes

- Pages, Files, or other tabs may be disabled on some courses. `canpull` will skip disabled tabs with a warning rather than aborting.
- Files with inaccessible download URLs (e.g. course images) are skipped with a yellow warning.
- Requires Python 3.13+.
