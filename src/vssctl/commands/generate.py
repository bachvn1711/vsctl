from typing import Optional
import shutil
import typer
from rich.console import Console
from rich.table import Table

from vssctl.core.catalog import CatalogService
from vssctl.core.tree_builder import TreeBuilder
from vssctl.core.generator import Generator
from vssctl.core.compiler import Compiler
from vssctl.core import paths

console = Console()


def parse_version_tuple(version_str: str):
    try:
        return tuple(int(x) for x in version_str.split("."))
    except ValueError:
        return (0,)


def run(
    version: Optional[str] = typer.Option(
        None,
        "--version",
        "-v",
        help="VSS release version to compile. If omitted, generates all supported versions.",
    )
):
    """
    Generate VSS project and compile to JSON.
    """
    from vssctl.config import settings

    # Resolve output directory
    target_out_dir = paths.resolve_path_gracefully(settings.output_dir)
    if not target_out_dir:
        target_out_dir = paths.GENERATED_DIR
    target_out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. Load catalog
        console.print("Loading catalog...")
        service = CatalogService()
        catalog = service.catalog
        
        # 2. Build tree
        console.print("Building signal tree...")
        builder = TreeBuilder()
        tree_root = builder.build(catalog)
        
        # 3. Generate company.vspec
        console.print("Generating company.vspec...")
        generator = Generator()
        generator.generate(tree_root)
        
        # 4. Compile Merged Environment
        console.print("Preparing merged environment...")
        compiler = Compiler()
        compiler.prepare_environment()
        
        if version is not None:
            # Mode A: Compile specific version
            resolved_version = version
            if resolved_version == "6.0" and settings.vss_version != "6.0" and not hasattr(version, "default"):
                resolved_version = settings.vss_version

            console.print(f"[blue]Starting compilation for VSS version {resolved_version}...[/blue]")
            output_path = paths.GENERATED_DIR / f"vss_release_{resolved_version}.json"
            compiler.compile(output_path)

            # Copy to output directory if different
            dest_path = target_out_dir / output_path.name
            if dest_path.resolve() != output_path.resolve():
                shutil.copy2(output_path, dest_path)

            console.print("Synchronizing custom signals across legacy JSON versions...")
            compiler.sync_all_json_versions(catalog)

            console.print(f"[green]Success! VSS release file created at '{dest_path}'.[/green]")
        else:
            # Mode B: Compile all supported versions
            console.print("[blue]No version specified. Generating all supported VSS release versions...[/blue]")
            
            # Compile main 6.0 release first
            default_version = "6.0"
            tmp_output_path = paths.GENERATED_DIR / f"vss_release_{default_version}.json"
            compiler.compile(tmp_output_path)
            
            # Synchronize custom signals across all VSS versions
            compiler.sync_all_json_versions(catalog)

            # Copy files from generated/json_tree/ and generated/ to the destination directory
            generated_files = []
            
            # Copy main compiled version
            dest_main = target_out_dir / tmp_output_path.name
            if tmp_output_path.exists():
                if dest_main.resolve() != tmp_output_path.resolve():
                    shutil.copy2(tmp_output_path, dest_main)
                generated_files.append((default_version, tmp_output_path.name, dest_main))

            # Copy synchronized legacy versions from generated/json_tree
            if paths.JSON_TREE_DIR.exists() and paths.JSON_TREE_DIR.is_dir():
                for item in paths.JSON_TREE_DIR.iterdir():
                    if item.is_file() and item.name.startswith("vss_release_") and item.name.endswith(".json"):
                        ver = item.name[len("vss_release_"):-len(".json")]
                        if ver != default_version:
                            dest_legacy = target_out_dir / item.name
                            if dest_legacy.resolve() != item.resolve():
                                shutil.copy2(item, dest_legacy)
                            generated_files.append((ver, item.name, dest_legacy))

            # Sort descending by version
            generated_files.sort(key=lambda x: parse_version_tuple(x[0]), reverse=True)

            # Render Summary Table
            table = Table(title="Generated VSS Version Release Files")
            table.add_column("Version", style="cyan", justify="center")
            table.add_column("File Name", style="green")
            table.add_column("Destination Output Path", style="blue")

            for ver, fname, fpath in generated_files:
                table.add_row(ver, fname, str(fpath))

            console.print("\n")
            console.print(table)
            console.print(f"\n[green]Success: All {len(generated_files)} VSS release versions generated successfully.[/green]")

    except Exception as e:
        console.print(f"[red]Error: Generation failed: {e}[/red]")
        raise typer.Exit(1)
