from pathlib import Path

from vssctl.core.storage import Storage
from vssctl.core.tree_builder import TreeBuilder
from vssctl.core.exporter import Exporter
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def main():

    #
    # Load catalog
    #
    catalog = Storage().load()

    print(f"Loaded {len(catalog.signals)} signals")

    #
    # Build tree
    #
    builder = TreeBuilder()

    tree = builder.build(catalog)

    #
    # Print tree
    #
    print("\n=== Tree ===")

    tree.dump()

    #
    # Export JSON
    #
    exporter = Exporter()

    exporter.export_tree_json(

        tree,

        PROJECT_ROOT / "workspace" / "generated" / "tree.json",

    )


if __name__ == "__main__":

    main()