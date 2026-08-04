from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from vssctl.web.app import create_app

console = Console()


def run(
    host: str = typer.Option("127.0.0.1", "--host", help="Host interface for the dashboard."),
    port: int = typer.Option(5555, "--port", min=1, max=65535, help="TCP port for the dashboard."),
    catalog_dir: Path | None = typer.Option(None, "--catalog-dir", file_okay=False, dir_okay=True, help="Directory containing team YAML catalogs."),
    debug: bool = typer.Option(False, "--debug/--no-debug", help="Enable Flask debug mode."),
) -> None:
    """Start the read-only vssctl web dashboard."""
    app = create_app(catalog_dir)
    console.print(f"[green]Dashboard: http://{host}:{port}[/green]")
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
