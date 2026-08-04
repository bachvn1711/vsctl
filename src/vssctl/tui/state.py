from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from vssctl.core.models import Catalog, Signal
from vssctl.core.storage import Storage
from vssctl.core.tree import TreeNode
from vssctl.core.tree_builder import TreeBuilder


class CatalogSource(StrEnum):
    BASE = "base"
    CUSTOM = "custom"
    MERGED = "merged"


class BrowserLoadError(RuntimeError):
    """Raised when the browser cannot load a usable catalog."""


@dataclass(frozen=True)
class BrowserState:
    source: CatalogSource
    catalog: Catalog
    tree: TreeNode

    @classmethod
    def load(cls, source: CatalogSource = CatalogSource.MERGED) -> "BrowserState":
        storage = Storage()
        try:
            catalog = _load_catalog(storage, source)
        except Exception as exc:
            raise BrowserLoadError(f"Unable to load {source.value} catalog: {exc}") from exc

        if not catalog.signals:
            raise BrowserLoadError(f"The {source.value} catalog is empty.")
        return cls(source=source, catalog=catalog, tree=TreeBuilder().build(catalog))


def _load_catalog(storage: Storage, source: CatalogSource) -> Catalog:
    if source is CatalogSource.BASE:
        return storage.load_base()
    if source is CatalogSource.CUSTOM:
        return storage.load_custom()

    base = storage.load_base()
    custom = storage.load_custom()
    merged: dict[tuple[str, str], Signal] = {
        (signal.parent, signal.name): signal for signal in base.signals
    }
    merged.update({(signal.parent, signal.name): signal for signal in custom.signals})
    return Catalog(version=custom.version or base.version, signals=list(merged.values()))


def matching_nodes(root: TreeNode, query: str) -> list[TreeNode]:
    normalized = query.strip().lower()
    if not normalized:
        return list(root.walk())
    return [node for node in root.walk() if _matches(node, normalized)]


def _matches(node: TreeNode, query: str) -> bool:
    signal = node.signal
    values = [node.name, node.path]
    if signal is not None:
        values.extend([signal.description, signal.datatype or "", signal.unit or ""])
    return any(query in value.lower() for value in values)
