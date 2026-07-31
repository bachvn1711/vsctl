import typer
from rich.console import Console
from vssctl.core.catalog import CatalogService
from vssctl.core.validator import Validator

console = Console()


def run():
    """
    Validate signals in the catalog against specifications and formatting rules.
    """
    console.print("[blue]Validating VSS catalog signals...[/blue]")
    try:
        service = CatalogService()
        signals = service.list()
    except Exception as e:
        console.print(f"[red]Error: Failed to load catalog: {e}[/red]")
        raise typer.Exit(1)

    if not signals:
        console.print("[yellow]Warning: Catalog is empty. Nothing to validate.[/yellow]")
        return

    validator = Validator()
    errors = []
    seen = set()

    for signal in signals:
        # 1. Check for duplicates
        sig_key = (signal.parent, signal.name)
        if sig_key in seen:
            errors.append(f"Duplicate signal definition: '{signal.parent}.{signal.name}'")
        else:
            seen.add(sig_key)

        # 2. Check signal structure/values
        try:
            validator.validate_name(signal)
            validator.validate_datatype(signal)
            validator.validate_parent(signal, service.catalog)
            validator.validate_description(signal)
            validator.validate_unit(signal)
        except Exception as err:
            errors.append(f"Signal '{signal.parent}.{signal.name}': {err}")

    if errors:
        console.print(f"[red]Validation failed! Found {len(errors)} error(s):[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise typer.Exit(1)

    console.print(f"[green]Success: Catalog is valid. Checked {len(signals)} signals.[/green]")
