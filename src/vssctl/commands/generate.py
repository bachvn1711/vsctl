import typer
from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.tree_builder import TreeBuilder
from vssctl.core.generator import Generator
from vssctl.core.compiler import Compiler

console = Console()


def run():
    """
    Generate VSS project and compile to JSON.
    """
    console.print("[blue]Starting generation process...[/blue]")
    
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
        compiler.compile()
        console.print("[green]✓ Generation successful! vss_release_6.0.json created.[/green]")
    except Exception as e:
        console.print(f"[red]✗ Generation failed: {e}[/red]")
        raise typer.Exit(1)
