import typer
from click.shell_completion import get_completion_class
from rich.console import Console
from typer.main import get_command

console = Console()


def run(
    shell: str = typer.Argument(
        ...,
        help="Target shell for autocompletion (bash, zsh, fish).",
    )
):
    """
    Generate shell completion scripts.
    """
    shell = shell.lower().strip()
    if shell not in ("bash", "zsh", "fish"):
        console.print(f"[red]Error: Unsupported shell '{shell}'. Use bash, zsh, or fish.[/red]")
        raise typer.Exit(1)

    try:
        from vssctl.cli import app

        completion_class = get_completion_class(shell)
        if completion_class is None:
            raise RuntimeError(f"No completion generator registered for {shell}.")
        generator = completion_class(
            get_command(app),
            {},
            "vssctl",
            "_VSSCTL_COMPLETE",
        )
        print(generator.source())
    except Exception as e:
        console.print(f"[red]Error: Failed to generate completion script: {e}[/red]")
        raise typer.Exit(1)
