import os
import re
import subprocess
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from vssctl.commands.build import find_latest_vss_file, get_vss_version, resolve_engine

console = Console()


def run_publish_flow(
    image: Optional[str],
    remote_tag: Optional[str],
    token: Optional[str],
    username: str,
    engine: str,
    skip_login: bool,
) -> str:
    """
    Internal helper executing the actual publish workflow.
    Returns the final remote URI.
    """
    # 1. Resolve container engine
    resolved_engine = resolve_engine(engine)
    console.print(f"Container engine: [cyan]{resolved_engine}[/cyan]")

    # 2. Resolve local image
    if image is None:
        latest_vss = find_latest_vss_file()
        vss_version = get_vss_version(latest_vss)
        local_image = f"kuksa-databroker:vss-{vss_version}"
    else:
        local_image = image
    console.print(f"Local image: [cyan]{local_image}[/cyan]")

    # 3. Verify local image exists
    inspect_res = subprocess.run([resolved_engine, "image", "inspect", local_image], capture_output=True, text=True)
    if inspect_res.returncode != 0:
        console.print(f"[red]Error: Local image '{local_image}' not found.[/red]")
        console.print("[yellow]Please build the image first using 'vssctl build'.[/yellow]")
        raise typer.Exit(1)

    # 4. Resolve remote tag and registry URI
    # Default remote tag: extract suffix from local image tag
    local_tag_suffix = local_image.split(":")[-1] if ":" in local_image else "latest"
    
    if remote_tag is None:
        resolved_remote_tag = local_tag_suffix
    else:
        resolved_remote_tag = remote_tag

    # If it is already a full URI, use it as is. Otherwise prepend GHCR pathway.
    if resolved_remote_tag.startswith("ghcr.io/"):
        remote_uri = resolved_remote_tag
    else:
        remote_uri = f"ghcr.io/{username}/databroker:{resolved_remote_tag}"

    console.print(f"Remote destination: [cyan]{remote_uri}[/cyan]")

    # 5. Authenticate if token is provided or found
    resolved_token = token
    if not resolved_token:
        resolved_token = os.environ.get("GHCR_TOKEN") or os.environ.get("CR_PAT")

    if not skip_login:
        if resolved_token:
            console.print("[blue]Logging into GitHub Container Registry (ghcr.io)...[/blue]")
            try:
                # Login using token via password-stdin
                subprocess.run(
                    [resolved_engine, "login", "ghcr.io", "-u", username, "--password-stdin"],
                    input=resolved_token,
                    capture_output=True,
                    text=True,
                    check=True
                )
                console.print("[green]Success: Authenticated to ghcr.io.[/green]")
            except subprocess.CalledProcessError as e:
                console.print("[red]Error: Authentication failed during login to ghcr.io.[/red]")
                if e.stderr:
                    console.print(f"[red]Details: {e.stderr.strip()}[/red]")
                console.print("[yellow]Troubleshooting tips:[/yellow]")
                console.print("  1. Verify your GitHub Personal Access Token (PAT) has the 'write:packages' scope.")
                console.print("  2. Ensure the username matches your GitHub account username.")
                console.print("  3. Set the GHCR_TOKEN or CR_PAT environment variable correctly.")
                raise typer.Exit(1)
        else:
            console.print("[yellow]Warning: No GitHub token provided or detected in environment. Attempting to push using existing session...[/yellow]")
    else:
        console.print("[blue]Skipping authentication step as requested.[/blue]")

    # 6. Tag the image
    console.print(f"Tagging [cyan]{local_image}[/cyan] as [cyan]{remote_uri}[/cyan]...")
    try:
        subprocess.run([resolved_engine, "tag", local_image, remote_uri], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error: Failed to tag image: {e.stderr or e}[/red]")
        raise typer.Exit(1)

    # 7. Push the image
    console.print(f"[blue]Pushing [cyan]{remote_uri}[/cyan] to GHCR...[/blue]")
    try:
        push_process = subprocess.Popen(
            [resolved_engine, "push", remote_uri],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        if push_process.stdout:
            for line in push_process.stdout:
                console.print(line.rstrip(), highlight=False, markup=False)
        push_process.wait()
        if push_process.returncode != 0:
            console.print(f"[red]Error: Push failed with return code {push_process.returncode}[/red]")
            raise typer.Exit(push_process.returncode)
    except Exception as e:
        console.print(f"[red]Error: Failed to execute push process: {e}[/red]")
        raise typer.Exit(1)

    console.print("\n[green]Success: Image published successfully![/green]")
    console.print(f"  Package URL: https://github.com/{username}?tab=packages")
    console.print(f"  Image URI:   {remote_uri}\n")

    return remote_uri


def run(
    image: Optional[str] = typer.Option(
        None,
        "--image",
        "-i",
        help="Local image name/tag built during build step.",
    ),
    remote_tag: Optional[str] = typer.Option(
        None,
        "--remote-tag",
        "-t",
        help="Remote tag or full registry URI to push to GHCR.",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="GitHub Personal Access Token (PAT) with write:packages scope.",
    ),
    username: str = typer.Option(
        "bachvn1711",
        "--username",
        help="GitHub username.",
    ),
    engine: str = typer.Option(
        "auto",
        "--engine",
        help="Container engine to execute push (auto, docker, podman).",
    ),
    skip_login: bool = typer.Option(
        False,
        "--skip-login",
        help="Skip authentication check/login step.",
    ),
):
    """
    Publish KUKSA Databroker image to GHCR.
    """
    console.print("[blue]Starting publication process...[/blue]")
    run_publish_flow(
        image=image,
        remote_tag=remote_tag,
        token=token,
        username=username,
        engine=engine,
        skip_login=skip_login,
    )
