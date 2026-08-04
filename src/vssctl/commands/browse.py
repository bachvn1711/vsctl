from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich.console import Console

from vssctl.tui.app import VssBrowserApp
from vssctl.tui.state import BrowserLoadError, BrowserState, CatalogSource

console = Console(stderr=True)


def run(
    source: Annotated[
        CatalogSource,
        typer.Option("--source", help="Catalog view to browse: base, custom, or merged."),
    ] = CatalogSource.MERGED,
) -> None:
    """Browse the catalog interactively in a terminal UI."""
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        console.print("[red]Error: vssctl browse requires an interactive terminal.[/red]")
        raise typer.Exit(1)

    try:
        state = BrowserState.load(source)
    except BrowserLoadError as exc:
        console.print(f"[red]Error: {exc}[/red]")
        raise typer.Exit(1) from exc

    try:
        VssBrowserApp(state).run()
    except (OSError, RuntimeError) as exc:
        console.print(f"[red]Error: Unable to start terminal browser: {exc}[/red]")
        raise typer.Exit(1) from exc
