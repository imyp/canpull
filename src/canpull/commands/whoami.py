from rich.console import Console

from canpull.client import CanvasClient

console = Console()


def whoami_cmd() -> None:
    """Show the currently authenticated Canvas user."""
    client = CanvasClient()
    user = client.get_one("/users/self")
    console.print(f"[green]Authorized[/green] as [bold]{user['name']}[/bold] (id: {user['id']})")
