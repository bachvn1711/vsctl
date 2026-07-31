import re
import shutil
import subprocess
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple
import typer
from rich.console import Console

from vssctl.core import paths

console = Console()


def check_engine_running(engine: str) -> bool:
    """
    Checks if a container engine executable exists and its daemon/service is active.
    """
    if not shutil.which(engine):
        return False
    try:
        # 'info' or 'version' commands are standard check targets.
        # 'ps' is also extremely fast. We'll use 'ps' or 'info'.
        # Since 'info' sometimes takes longer or requires authentication depending on daemon,
        # 'ps' is a standard minimal operation.
        res = subprocess.run([engine, "ps"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def resolve_engine(choice: str) -> str:
    """
    Resolves container engine based on preference (podman first, then docker).
    Raises typer.Exit if requested engine is not running/available.
    """
    choice = choice.lower().strip()
    if choice == "auto":
        if check_engine_running("podman"):
            return "podman"
        if check_engine_running("docker"):
            return "docker"
        console.print("[red]Error: Neither podman nor docker is installed and running.[/red]")
        raise typer.Exit(1)
    elif choice in ("podman", "docker"):
        if not shutil.which(choice):
            console.print(f"[red]Error: Container engine '{choice}' is not installed (executable not found).[/red]")
            raise typer.Exit(1)
        if not check_engine_running(choice):
            console.print(f"[red]Error: Container engine '{choice}' is installed but not running.[/red]")
            raise typer.Exit(1)
        return choice
    else:
        console.print(f"[red]Error: Unsupported container engine choice '{choice}'. Use auto, docker, or podman.[/red]")
        raise typer.Exit(1)


def parse_version_tuple(version_str: str) -> Tuple[int, ...]:
    """
    Parses version string into a numeric tuple for sorting.
    """
    try:
        return tuple(int(x) for x in version_str.split("."))
    except ValueError:
        return (0,)


def find_latest_vss_file() -> Path:
    """
    Finds the latest generated vss_release_*.json file in generated directories.
    """
    search_dirs = [paths.GENERATED_DIR, paths.JSON_TREE_DIR]
    vss_files = []

    for sdir in search_dirs:
        if sdir.exists() and sdir.is_dir():
            for item in sdir.iterdir():
                if item.is_file() and item.name.startswith("vss_release_") and item.name.endswith(".json"):
                    # Extract version part: vss_release_6.0.json -> 6.0
                    ver_str = item.name[len("vss_release_"):-len(".json")]
                    ver_tuple = parse_version_tuple(ver_str)
                    vss_files.append((ver_tuple, ver_str, item))

    if not vss_files:
        console.print("[red]Error: No generated VSS metadata JSON files found (e.g. vss_release_*.json).[/red]")
        console.print("[yellow]Please run 'vssctl generate' first to create VSS release files.[/yellow]")
        raise typer.Exit(1)

    # Sort descending by version tuple
    vss_files.sort(key=lambda x: x[0], reverse=True)
    latest_file = vss_files[0][2]
    console.print(f"Using default latest VSS file: [cyan]{latest_file.name}[/cyan]")
    return latest_file


def get_vss_version(vss_file_path: Path) -> str:
    """
    Extracts version string from a given VSS filename or defaults to 'latest'.
    """
    filename = vss_file_path.name
    # Standard: vss_release_6.0.json -> 6.0
    match = re.search(r"vss_release_(\d+(?:\.\d+)*)", filename)
    if match:
        return match.group(1)
    # Generic: match any sequence of digits separated by dots
    match = re.search(r"(\d+(?:\.\d+)*)", filename)
    if match:
        return match.group(1)
    return "latest"


def find_build_context(databroker_dir: Path) -> Path:
    """
    Verifies databroker workspace and returns the directory holding Cargo.toml.
    """
    if (databroker_dir / "Cargo.toml").exists() and (databroker_dir / "databroker").exists():
        return databroker_dir
    sub_dir = databroker_dir / "kuksa-databroker"
    if sub_dir.exists() and (sub_dir / "Cargo.toml").exists():
        return sub_dir

    console.print(f"[red]Error: Valid Kuksa Databroker workspace root not found at '{databroker_dir}'.[/red]")
    console.print("[yellow]Ensure the directory exists and contains Cargo.toml or 'kuksa-databroker/Cargo.toml'.[/yellow]")
    raise typer.Exit(1)


def run(
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
        help="Container engine choice (auto, docker, podman). Default: auto (detects podman first).",
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
        help="GitHub Personal Access Token (PAT) with write:packages scope (used if publishing).",
    ),
    username: str = typer.Option(
        "bachvn1711",
        "--username",
        help="GitHub username (used if publishing).",
    ),
    remote_tag: Optional[str] = typer.Option(
        None,
        "--remote-tag",
        help="Remote tag or full registry URI to push to GHCR (used if publishing).",
    ),
    skip_login: bool = typer.Option(
        False,
        "--skip-login",
        help="Skip authentication check/login step (used if publishing).",
    ),
):
    """
    Build customized KUKSA Databroker Docker/Podman image.
    """
    console.print("[blue]Pre-flight checks...[/blue]")

    # 1. Resolve container engine
    resolved_engine = resolve_engine(engine)
    console.print(f"Container engine: [cyan]{resolved_engine}[/cyan]")

    # 2. Resolve databroker directory
    if databroker_dir is None:
        from vssctl.config import settings
        databroker_dir = paths.resolve_path_gracefully(settings.databroker_path)
        if databroker_dir is None:
            databroker_dir = paths.WORKSPACE / "databroker"
    else:
        databroker_dir = paths.resolve_path_gracefully(databroker_dir)
    build_context = find_build_context(databroker_dir)
    console.print(f"Databroker directory: [cyan]{build_context}[/cyan]")

    # 3. Resolve VSS file
    if vss_file is None:
        resolved_vss_file = find_latest_vss_file()
    else:
        resolved_vss_file = paths.resolve_path_gracefully(vss_file)
        if not resolved_vss_file or not resolved_vss_file.exists():
            console.print(f"[red]Error: VSS file not found at '{vss_file}'[/red]")
            raise typer.Exit(1)
    console.print(f"Metadata file: [cyan]{resolved_vss_file}[/cyan]")

    # 4. Resolve tag
    vss_version = get_vss_version(resolved_vss_file)
    if tag is None:
        resolved_tag = f"kuksa-databroker:vss-{vss_version}"
    else:
        resolved_tag = tag
    console.print(f"Target image tag: [cyan]{resolved_tag}[/cyan]")

    # 5. Check for pre-built binaries to decide on Dockerfile pattern
    machine = platform.machine().lower()
    if "amd64" in machine or "x86_64" in machine:
        docker_arch = "amd64"
    elif "arm64" in machine or "aarch64" in machine:
        docker_arch = "arm64"
    else:
        docker_arch = "amd64"

    candidate_binaries = [
        Path(f"dist/{docker_arch}/databroker"),
        Path("dist/databroker"),
        Path("target/release/databroker"),
    ]

    prebuilt_rel_path = None
    for rel_path in candidate_binaries:
        if (build_context / rel_path).exists():
            prebuilt_rel_path = rel_path
            break

    # 6. Generate tailored Dockerfile contents
    dockerfile_lines = []
    if prebuilt_rel_path:
        console.print(f"[green]Found pre-built binary at '{prebuilt_rel_path}'. Skipping compilation phase.[/green]")
        # Use simple copy build
        prebuilt_rel_path_posix = prebuilt_rel_path.as_posix()
        dockerfile_lines = [
            "FROM debian:bookworm-slim",
            "WORKDIR /app",
            f"COPY {prebuilt_rel_path_posix} /app/databroker",
            "COPY vss_release.json /app/vss_release.json",
            "ENV KUKSA_DATABROKER_ADDR=0.0.0.0",
            "ENV KUKSA_DATABROKER_PORT=55555",
            "ENV KUKSA_DATABROKER_METADATA_FILE=/app/vss_release.json",
            "EXPOSE 55555",
            "ENTRYPOINT [ \"/app/databroker\" ]"
        ]
    else:
        console.print("[yellow]No pre-built databroker binary found. Using multi-stage container build (will compile from source).[/yellow]")
        dockerfile_lines = [
            "FROM rust:1-slim AS builder",
            "RUN apt-get update && apt-get install -y --no-install-recommends \\",
            "    protobuf-compiler \\",
            "    cmake \\",
            "    make \\",
            "    g++ \\",
            "    libssl-dev \\",
            "    pkg-config \\",
            "    && rm -rf /var/lib/apt/lists/*",
            "WORKDIR /build",
            "COPY . .",
            "RUN cargo build --release --bin databroker",
            "",
            "FROM debian:bookworm-slim",
            "WORKDIR /app",
            "COPY --from=builder /build/target/release/databroker /app/databroker",
            "COPY vss_release.json /app/vss_release.json",
            "ENV KUKSA_DATABROKER_ADDR=0.0.0.0",
            "ENV KUKSA_DATABROKER_PORT=55555",
            "ENV KUKSA_DATABROKER_METADATA_FILE=/app/vss_release.json",
            "EXPOSE 55555",
            "ENTRYPOINT [ \"/app/databroker\" ]"
        ]

    # Write files to build context
    temp_dockerfile = build_context / "Dockerfile.vssctl"
    temp_vss = build_context / "vss_release.json"

    proto_symlink_path = build_context / "databroker-proto" / "proto"
    actual_proto_path = build_context / "proto"

    is_symlink_file = False
    symlink_content = ""

    try:
        # Resolve Windows git symlink issue for proto directory:
        # If it is a file containing '../proto/', temporarily replace it with the actual directory
        if proto_symlink_path.exists() and proto_symlink_path.is_file():
            is_symlink_file = True
            with open(proto_symlink_path, "r", encoding="utf-8") as sf:
                symlink_content = sf.read()
            
            console.print("[blue]Resolving git symlink for proto directory...[/blue]")
            proto_symlink_path.unlink()
            shutil.copytree(actual_proto_path, proto_symlink_path)

        # Copy the VSS file to context
        shutil.copy2(resolved_vss_file, temp_vss)

        # Write Dockerfile.vssctl
        with open(temp_dockerfile, "w", encoding="utf-8") as df:
            df.write("\n".join(dockerfile_lines) + "\n")

        # Execute container build
        console.print(f"[blue]Starting container build using {resolved_engine}...[/blue]")
        
        build_cmd = [resolved_engine, "build", "-f", "Dockerfile.vssctl", "-t", resolved_tag]
        if no_cache:
            build_cmd.append("--no-cache")
        build_cmd.append(".")

        # Launch process and stream logs in real time
        process = subprocess.Popen(
            build_cmd,
            cwd=str(build_context),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Print logs line by line
        if process.stdout:
            for line in process.stdout:
                console.print(line.rstrip(), highlight=False, markup=False)

        process.wait()

        if process.returncode != 0:
            console.print(f"[red]Error: Build failed with return code {process.returncode}[/red]")
            raise typer.Exit(process.returncode)

        console.print("\n[green]Success: Customized Kuksa Databroker image built successfully![/green]")
        console.print(f"Image Tag: [cyan]{resolved_tag}[/cyan]")
        console.print("\n[blue]How to run your customized Databroker container:[/blue]")
        console.print(f"  {resolved_engine} run -it --rm -p 55555:55555 {resolved_tag}\n")

        if isinstance(publish, bool) and publish:
            console.print("[blue]Invoking publication flow directly after successful build...[/blue]")
            from vssctl.commands.publish import run_publish_flow
            run_publish_flow(
                image=resolved_tag,
                remote_tag=remote_tag,
                token=token,
                username=username,
                engine=resolved_engine,
                skip_login=skip_login,
            )

    except Exception as e:
        console.print(f"[red]Error: An unexpected failure occurred during build process: {e}[/red]")
        raise typer.Exit(1)
    finally:
        # Clean up temporary context artifacts
        if temp_dockerfile.exists():
            temp_dockerfile.unlink()
        if temp_vss.exists():
            temp_vss.unlink()

        # Restore git symlink if we replaced it
        if is_symlink_file:
            try:
                if proto_symlink_path.is_dir():
                    shutil.rmtree(proto_symlink_path)
                elif proto_symlink_path.exists():
                    proto_symlink_path.unlink()
                
                with open(proto_symlink_path, "w", encoding="utf-8", newline="\n") as sf:
                    sf.write(symlink_content)
                console.print("[blue]Restored proto directory git symlink.[/blue]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to restore symlink: {e}[/yellow]")