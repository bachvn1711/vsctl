from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class TreeNode:
    """
    Generic VSS tree node.

    Branch nodes:
        signal = None

    Signal nodes:
        signal = Signal(...)
    """

    name: str
    signal: Optional[Any] = None
    parent: Optional["TreeNode"] = None

    children: dict[str, "TreeNode"] = field(default_factory=dict)

    @property
    def is_root(self) -> bool:
        return self.parent is None

    @property
    def is_signal(self) -> bool:
        return self.signal is not None

    @property
    def is_branch(self) -> bool:
        return self.signal is None

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name

        return f"{self.parent.path}.{self.name}"

    def add_child(self, node: "TreeNode") -> None:
        node.parent = self
        self.children[node.name] = node

    def has_child(self, name: str) -> bool:
        return name in self.children

    def get_child(self, name: str) -> Optional["TreeNode"]:
        return self.children.get(name)

    def find(self, path: str) -> Optional["TreeNode"]:

        if self.path == path:
            return self

        for child in self.children.values():
            result = child.find(path)

            if result is not None:
                return result

        return None

    def walk(self):
        """
        DFS traversal.
        """

        yield self

        for child in self.children.values():
            yield from child.walk()

    def dump(self, level: int = 0):

        prefix = "    " * level

        icon = "📄" if self.is_signal else "📁"

        print(f"{prefix}{icon} {self.name}")

        for child in self.children.values():
            child.dump(level + 1)

    def to_dict(self):

        return {
            "name": self.name,
            "path": self.path,
            "type": "signal" if self.is_signal else "branch",
            "children": [
                child.to_dict()
                for child in self.children.values()
            ],
        }