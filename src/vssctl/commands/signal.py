import typer
from rich.console import Console

from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal
from vssctl.core.exceptions import ValidationError

app = typer.Typer()

console = Console()


@app.command()
def list():
    service = CatalogService()
    signals = service.list()

    if not signals:
        console.print("[yellow]No signals found.[/yellow]")
        return

    for signal in signals:
        console.print(
            f"{signal.parent}.{signal.name}"
        )


@app.command()
def add():
    while True:
        # Prompt without a default argument to prevent typer from appending the '[signal]' suffix
        node_type = typer.prompt("Node type (signal/branch)").lower().strip()
        if node_type in ("signal", "branch"):
            break
        console.print("[red]Error: Invalid choice. You must enter either 'signal' or 'branch'.[/red]")

    parent = typer.prompt("Parent")
    name = typer.prompt("Name")
    description = typer.prompt("Description")

    if node_type == "branch":
        signal = Signal(
            parent=parent,
            name=name,
            datatype=None,
            description=description,
        )
    else:
        datatype = typer.prompt("Datatype")
        unit = typer.prompt("Unit", default="")

        signal = Signal(
            parent=parent,
            name=name,
            datatype=datatype,
            description=description,
            unit=unit or None,
        )

    try:
        CatalogService().add(signal)
        console.print("[green]Success: Node added[/green]")
    except ValidationError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def remove(
    path: str = typer.Argument(
        ...,
        help="Full dot-separated path of the signal/branch to remove (e.g. Vehicle.ADAS.RPM).",
    )
):
    """
    Remove a signal or branch. If it is a branch, deletes all child signals under it.
    """
    path = path.strip()
    if not path:
        console.print("[red]Error: Path is required.[/red]")
        raise typer.Exit(1)
        
    # Normalize spelling using a dummy Signal model validator
    try:
        dummy = Signal(parent=path, name="Dummy", datatype="int32")
        normalized_path = dummy.parent
    except Exception:
        normalized_path = path
        
    service = CatalogService()
    signals = service.list()
    
    # Decompose normalized_path into parent and name
    parts = normalized_path.split(".")
    target_parent = ".".join(parts[:-1])
    target_name = parts[-1]
    
    new_signals = []
    deleted_count = 0
    
    for s in signals:
        is_target = (s.parent == target_parent and s.name == target_name)
        is_child = (s.parent == normalized_path or s.parent.startswith(normalized_path + "."))
        
        if is_target or is_child:
            deleted_count += 1
        else:
            new_signals.append(s)
            
    if deleted_count > 0:
        service.catalog.signals = new_signals
        service.storage.save(service.catalog)
        console.print(f"[green]Success: Removed target and its {deleted_count - 1} child signal(s).[/green]")
    else:
        console.print(f"[yellow]Warning: Target path '{normalized_path}' not found in catalog.[/yellow]")


@app.command()
def search(keyword: str):
    results = CatalogService().search(keyword)

    if not results:
        console.print("[yellow]No matching signals.[/yellow]")
        return

    for signal in results:
        console.print(
            f"{signal.parent}.{signal.name}"
        )


@app.command()
def update(
    version: str = typer.Option(
        "6.0",
        "--version",
        "-v",
        help="VSS baseline version to update from.",
    )
):
    """
    Generate/update catalog signals.yaml with all branches from baseline VSS JSON.
    """
    console.print(f"[blue]Updating signals.yaml branches from VSS baseline version {version}...[/blue]")
    
    from vssctl.core import paths
    template_name = f"vss_release_{version}.json"
    template_path = paths.VSS_CORE_TEMPLATES / template_name
    if not template_path.exists():
        template_path = paths.resolve_path_gracefully(template_path)
        if not template_path or not template_path.exists():
            console.print(f"[red]Error: Baseline JSON not found for version {version}.[/red]")
            raise typer.Exit(1)
            
    try:
        import json
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error: Failed to load baseline JSON: {e}[/red]")
        raise typer.Exit(1)
        
    branches = []
    def recurse(node, prefix=""):
        if not isinstance(node, dict):
            return
        for key, val in node.items():
            if isinstance(val, dict):
                if key in ("children", "description", "type", "datatype", "unit", "writable", "minimum", "maximum", "uuid"):
                    continue
                current_path = f"{prefix}.{key}" if prefix else key
                if current_path == "Vehicle":
                    if "children" in val:
                        recurse(val["children"], current_path)
                    continue

                node_type = val.get("type")
                if node_type == "branch" or "children" in val:
                    parts = current_path.split(".")
                    parent_path = ".".join(parts[:-1])
                    name = parts[-1]
                    description = val.get("description", f"Baseline branch {name}")
                    branches.append({
                        "parent": parent_path,
                        "name": name,
                        "datatype": None,
                        "description": description
                    })
                
                if "children" in val:
                    recurse(val["children"], current_path)
    recurse(data)
    
    service = CatalogService()
    existing_signals = service.list()
    existing_keys = {(s.parent, s.name) for s in existing_signals}
    
    added_count = 0
    for b in branches:
        key = (b["parent"], b["name"])
        if key not in existing_keys:
            sig = Signal(
                parent=b["parent"],
                name=b["name"],
                datatype=None,
                description=b["description"]
            )
            service.catalog.signals.append(sig)
            existing_keys.add(key)
            added_count += 1
            
    if added_count > 0:
        service.storage.save(service.catalog)
        console.print(f"[green]Success: Catalog updated! Added {added_count} baseline branches to signals.yaml.[/green]")
    else:
        console.print("[yellow]Catalog is already up to date with baseline branches.[/yellow]")