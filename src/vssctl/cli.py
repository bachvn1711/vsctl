#!/usr/bin/env python3

import typer

from vssctl.commands import doctor
from vssctl.commands import signal
from vssctl.commands import generate

app = typer.Typer(
    name="vssctl",
    help="Vehicle Signal Specification Management Tool",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(
    signal.app,
    name="signal",
    help="Manage VSS signals",
)

# Register standalone commands
app.command(help="Check local environment")(doctor.run)
app.command(name="generate", help="Generate VSS project and compile")(generate.run)

def main():
    app()


if __name__ == "__main__":
    main()