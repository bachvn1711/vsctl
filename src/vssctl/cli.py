#!/usr/bin/env python3

import typer

from vssctl.commands import doctor
from vssctl.commands import signal
from vssctl.commands import generate
from vssctl.commands import build
from vssctl.commands import publish

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
app.command(name="doctor", help="Check local environment")(doctor.run)
app.command(name="generate", help="Generate VSS project and compile")(generate.run)
app.command(name="build", help="Build Databroker Docker/Podman image")(build.run)
app.command(name="publish", help="Publish Databroker image to GHCR")(publish.run)

def main():
    app()


if __name__ == "__main__":
    main()