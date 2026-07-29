from __future__ import annotations

from vssctl.core.models import Catalog, Signal
from vssctl.core.tree import TreeNode


class TreeBuilder:

    def build(
        self,
        catalog: Catalog,
    ) -> TreeNode:

        root = TreeNode("Vehicle")

        for signal in catalog.signals:

            self._insert(root, signal)

        return root

    def _insert(
        self,
        root: TreeNode,
        signal: Signal,
    ) -> None:

        #
        # Vehicle.ADAS.Speed
        #
        parts = signal.parent.split(".")

        current = root

        #
        # Skip "Vehicle"
        #
        for part in parts[1:]:

            child = current.get_child(part)

            if child is None:

                child = TreeNode(part)

                current.add_child(child)

            current = child

        #
        # Add signal node
        #
        if not current.has_child(signal.name):

            current.add_child(

                TreeNode(

                    name=signal.name,

                    signal=signal,

                )

            )