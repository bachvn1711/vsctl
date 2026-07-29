from vssctl.core.paths import TREE_JSON
from vssctl.core.storage import Storage
from vssctl.core.tree_builder import TreeBuilder
from vssctl.core.exporter import Exporter


def main():

    catalog = Storage().load()

    tree = TreeBuilder().build(catalog)

    tree.dump()

    Exporter().export_tree_json(
        tree,
        TREE_JSON,
    )


if __name__ == "__main__":
    main()