import typer

from vssctl.commands import doctor
from vssctl.commands import signal

app = typer.Typer()

app.add_typer(
    signal.app,
    name="signal",
)

app.command()(doctor.run)


if __name__ == "__main__":
    app()