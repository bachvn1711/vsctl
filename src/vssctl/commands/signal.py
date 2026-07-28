import typer

from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal
from vssctl.core.exceptions import ValidationError

app = typer.Typer()

console = Console()


@app.command()
def list():

    service = CatalogService()

    signals = service.list()

    if not signals:
        console.print("[yellow]No signals found.[/yellow]")
        return

    for signal in signals:
        console.print(
            f"{signal.parent}.{signal.name}"
        )


@app.command()
def add():

    parent = typer.prompt("Parent")

    name = typer.prompt("Signal name")

    datatype = typer.prompt("Datatype")

    description = typer.prompt("Description")

    unit = typer.prompt("Unit", default="")

    signal = Signal(
        parent=parent,
        name=name,
        datatype=datatype,
        description=description,
        unit=unit or None,
    )

    try:

        CatalogService().add(signal)

        console.print("[green]✓ Signal added[/green]")

    except ValidationError as e:

        console.print(f"[red]✗ {e}[/red]")

        raise typer.Exit(1)


@app.command()
def remove(parent: str, name: str):

    CatalogService().remove(parent, name)

    console.print("[green]✓ Removed[/green]")


@app.command()
def search(keyword: str):

    results = CatalogService().search(keyword)

    if not results:

        console.print("[yellow]No matching signals.[/yellow]")

        return

    for signal in results:

        console.print(
            f"{signal.parent}.{signal.name}"
        )