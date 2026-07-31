import typer
from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.tree_builder import TreeBuilder
import typer
from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.tree_builder import TreeBuilder
from vssctl.core.generator import Generator
from vssctl.core.compiler import Compiler
from vssctl.core import paths

console = Console()


def run(
    version: str = typer.Option(
        "6.0",
        "--version",
        help="VSS release version to compile.",
    )
):
    """
    Generate VSS project and compile to JSON.
    """
    from vssctl.config import settings
    resolved_version = version
    if resolved_version == "6.0" and settings.vss_version != "6.0" and not hasattr(version, "default"):
        resolved_version = settings.vss_version

    console.print(f"[blue]Starting generation process for VSS version {resolved_version}...[/blue]")
    
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
        
        # 4. Compile
        console.print("Preparing merged environment...")
        compiler = Compiler()
        compiler.prepare_environment()
        
        console.print("Invoking official VSS compiler...")
        output_path = paths.GENERATED_DIR / f"vss_release_{resolved_version}.json"
        compiler.compile(output_path)

        console.print("Synchronizing custom signals across all release JSON versions...")
        compiler.sync_all_json_versions(catalog)

        console.print(f"[green]Success! VSS release file created at '{output_path.name}'.[/green]")
    except Exception as e:
        console.print(f"[red]Error: Generation failed: {e}[/red]")
        raise typer.Exit(1)
