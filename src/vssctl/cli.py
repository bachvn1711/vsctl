#!/usr/bin/env python3

from pathlib import Path
from typing import Optional
import typer

from vssctl.commands import doctor
from vssctl.commands import signal
from vssctl.commands import generate
from vssctl.commands import build
from vssctl.commands import publish
from vssctl.commands import validate
from vssctl.commands import pipeline
from vssctl.commands import completion
from vssctl.commands import browse

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
app.command(name="validate", help="Validate VSS catalog signals against specs")(validate.run)
app.command(name="pipeline", help="Run the complete spec workflow (Validate -> Generate -> Build -> Publish)")(pipeline.run)
app.command(name="completion", help="Generate shell completion scripts")(completion.run)
app.command(name="browse", help="Browse the signal tree interactively")(browse.run)
app.command(name="remove", help="Remove custom signals")(signal.remove)


@app.callback()
def main(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to custom .vssctl.yaml config file.",
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose log output.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Enable quiet mode (suppress output logs).",
    ),
):
    """
    Global CLI setup callback. Loads configuration and settings.
    """
    from vssctl.config import settings
    settings.load(config)
    settings.verbose = verbose
    settings.quiet = quiet


def main_entry():
    app()


if __name__ == "__main__":
    main_entry()
