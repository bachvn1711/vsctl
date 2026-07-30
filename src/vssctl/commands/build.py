import subprocess
from rich.console import Console

console = Console()


def run():
    """
    Build KUKSA Databroker Docker/Podman image.
    """
    console.print("[blue]Building KUKSA Databroker image...[/blue]")
    try:
        subprocess.run(
            [
                "podman",
                "build",
                "-t",
                "ghcr.io/bachvn1711/databroker:v1.0.0",
                ".",
            ],
            check=True,
        )
        console.print("[green]Success: Image built successfully.[/green]")
    except Exception as e:
        console.print(f"[red]Error: Build failed: {e}[/red]")