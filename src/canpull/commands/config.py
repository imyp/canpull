import typer
from rich.console import Console

from canpull.config import (
    CONFIG_FILE,
    get_base_url,
    get_downloads_dir,
    save_config,
)
from canpull.config import (
    get_token as _get_token_from_config,
)

console = Console()


def config_cmd() -> None:
    """Interactively set up canpull configuration.

    Prompts for Canvas API token, base URL, and downloads directory.
    Values are saved to ~/.config/canpull/config.ini.
    Current values (if any) are shown as defaults.
    """
    console.print(f"Configuring canpull — saved to [bold]{CONFIG_FILE}[/bold]\n")

    token = typer.prompt(
        "Canvas API token",
        default=_get_token_from_config() if CONFIG_FILE.exists() else "",
        hide_input=True,
    )
    url = typer.prompt(
        "Canvas base URL",
        default=get_base_url(),
    )
    downloads_dir = typer.prompt(
        "Default downloads directory",
        default=str(get_downloads_dir()),
    )

    save_config(token=token, url=url.rstrip("/"), downloads_dir=downloads_dir)
    console.print(f"\n[green]Configuration saved to[/green] [bold]{CONFIG_FILE}[/bold]")
