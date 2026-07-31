import os
import sys
import subprocess
import typer
from rich.console import Console

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

    # Click auto-completion setup env var
    env_var = "_VSSCTL_COMPLETE"
    val = f"{shell}_source"

    try:
        env = os.environ.copy()
        env[env_var] = val
        # Execute the module to trigger Click's completion generation output
        res = subprocess.run(
            [sys.executable, "-m", "vssctl.cli"],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print(res.stdout)
    except Exception as e:
        console.print(f"[red]Error: Failed to generate completion script: {e}[/red]")
        raise typer.Exit(1)
