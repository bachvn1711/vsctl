from pathlib import Path
from typing import Optional
import typer
from rich.console import Console

from vssctl.commands import validate, generate, build

console = Console()


def run(
    version: str = typer.Option(
        "6.0",
        "--version",
        help="VSS release version to validate and compile.",
    ),
    vss_file: Optional[Path] = typer.Option(
        None,
        "--vss-file",
        "-f",
        help="Path to the generated VSS metadata JSON. Default to latest if omitted.",
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help="Output image tag. Default format: kuksa-databroker:vss-<version>",
    ),
    engine: str = typer.Option(
        "auto",
        "--engine",
        help="Container engine choice (auto, docker, podman). Default: auto.",
    ),
    databroker_dir: Optional[Path] = typer.Option(
        None,
        "--databroker-dir",
        help="Path to the databroker workspace directory. Defaults to workspace/databroker.",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Do not use cache when building the image.",
    ),
    publish: bool = typer.Option(
        False,
        "--publish",
        "-p",
        help="Publish the built image directly to GHCR.",
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
    remote_tag: Optional[str] = typer.Option(
        None,
        "--remote-tag",
        help="Remote tag or registry URI to push to GHCR.",
    ),
    skip_login: bool = typer.Option(
        False,
        "--skip-login",
        help="Skip authentication check/login step.",
    ),
):
    """
    Run the complete VSS spec workflow: Validate -> Generate -> Build -> (Optional) Publish.
    """
    console.print("[blue]Executing complete VSS pipeline...[/blue]")

    # 1. Validation Step
    console.print("\n[blue]>>> Step 1/3: Validating Catalog Specs[/blue]")
    validate.run()

    # 2. Generation Step
    console.print("\n[blue]>>> Step 2/3: Generating VSS Metadata Release File[/blue]")
    generate.run(version=version)

    # 3. Build & Publish Steps
    console.print("\n[blue]>>> Step 3/3: Building customized Kuksa Databroker Container Image[/blue]")
    build.run(
        vss_file=vss_file,
        tag=tag,
        engine=engine,
        databroker_dir=databroker_dir,
        no_cache=no_cache,
        publish=publish,
        token=token,
        username=username,
        remote_tag=remote_tag,
        skip_login=skip_login,
    )

    console.print("\n[green]Success: Full local pipeline completed successfully![/green]")
