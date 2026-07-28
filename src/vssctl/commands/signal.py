import typer

from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal

console = Console()

app = typer.Typer()


@app.command()
def list():

    service = CatalogService()

    for signal in service.list():

        console.print(
            f"{signal.parent}.{signal.name}"
        )


@app.command()
def add():

    parent = typer.prompt("Parent")

    name = typer.prompt("Signal")

    datatype = typer.prompt("Datatype")

    description = typer.prompt("Description")

    signal = Signal(

        parent=parent,

        name=name,

        datatype=datatype,

        description=description,

    )

    CatalogService().add(signal)

    console.print("[green]Signal added[/green]")