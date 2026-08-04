from __future__ import annotations

from textual.widgets import Tree
from textual.widgets.tree import TreeNode as TextualTreeNode

from vssctl.core.tree import TreeNode


class CatalogTree(Tree[TreeNode]):
    """Textual tree populated from the domain tree."""

    def load_domain_tree(self, root: TreeNode, visible_paths: set[str] | None = None) -> None:
        self.clear()
        root_node = self.root.add(root.name, data=root)
        self._add_children(root_node, root, visible_paths)
        root_node.expand()

    def _add_children(
        self,
        target: TextualTreeNode[TreeNode],
        source: TreeNode,
        visible_paths: set[str] | None,
    ) -> None:
        for child in source.children.values():
            if visible_paths is not None and child.path not in visible_paths:
                continue
            child_node = target.add(self._label(child), data=child)
            self._add_children(child_node, child, visible_paths)

    @staticmethod
    def _label(node: TreeNode) -> str:
        return f"[S] {node.name}" if node.is_signal else f"[B] {node.name}"
