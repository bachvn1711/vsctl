from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class CatalogLoadError(RuntimeError):
    """Raised when a team catalog cannot be read or has an invalid shape."""


@dataclass(frozen=True)
class CatalogSignal:
    path: str
    name: str
    parent: str
    datatype: str | None
    description: str
    unit: str | None
    writable: bool
    minimum: float | None
    maximum: float | None
    allowed: list[str] | None
    owner: str
    since: str | None
    source: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "parent": self.parent,
            "type": "branch" if self.datatype is None else ("actuator" if self.writable else "sensor"),
            "datatype": self.datatype,
            "description": self.description,
            "unit": self.unit,
            "writable": self.writable,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "allowed": self.allowed,
            "owner": self.owner,
            "since": self.since,
            "source": self.source,
        }


@dataclass(frozen=True)
class CatalogAggregate:
    signals: list[CatalogSignal]
    duplicates: list[str]

    def filtered(self, owner: str | None, datatype: str | None, since: str | None) -> list[CatalogSignal]:
        return [
            signal
            for signal in self.signals
            if (owner is None or signal.owner == owner)
            and (datatype is None or signal.datatype == datatype)
            and (since is None or signal.since == since)
        ]

    def tree(self) -> dict[str, Any]:
        root: dict[str, Any] = {"name": "Vehicle", "path": "Vehicle", "type": "branch", "children": {}}
        for signal in self.signals:
            parts = signal.path.split(".")
            if not parts or parts[0] != "Vehicle":
                continue
            current = root
            for index, part in enumerate(parts[1:], start=1):
                children = current["children"]
                if index == len(parts) - 1:
                    node = signal.as_dict()
                    node["children"] = {}
                    children[part] = node
                else:
                    current = children.setdefault(
                        part,
                        {"name": part, "path": ".".join(parts[: index + 1]), "type": "branch", "children": {}},
                    )
        return _serialise_tree(root)

    def teams(self) -> list[dict[str, Any]]:
        grouped: dict[str, list[CatalogSignal]] = {}
        for signal in self.signals:
            grouped.setdefault(signal.owner, []).append(signal)
        return [
            {"name": name, "signal_count": len(signals), "signals": [signal.as_dict() for signal in signals]}
            for name, signals in sorted(grouped.items())
        ]

    def stats(self) -> dict[str, Any]:
        datatype_counts = Counter(signal.datatype or "branch" for signal in self.signals)
        version_counts = Counter(signal.since or "unspecified" for signal in self.signals)
        return {
            "total_signals": sum(signal.datatype is not None for signal in self.signals),
            "total_branches": sum(signal.datatype is None for signal in self.signals),
            "total_nodes": len(self.signals),
            "team_count": len({signal.owner for signal in self.signals}),
            "datatype_distribution": dict(sorted(datatype_counts.items())),
            "version_distribution": dict(sorted(version_counts.items())),
            "duplicate_paths": self.duplicates,
        }


class CatalogAggregator:
    """Read-only aggregation of per-team YAML catalogs."""

    def __init__(self, catalog_dir: Path) -> None:
        self.catalog_dir = catalog_dir

    def load(self) -> CatalogAggregate:
        if not self.catalog_dir.is_dir():
            raise CatalogLoadError(f"Catalog directory does not exist: {self.catalog_dir}")
        indexed: dict[str, CatalogSignal] = {}
        duplicates: list[str] = []
        for path in sorted(self.catalog_dir.glob("*.yaml")):
            for signal in self._load_file(path):
                if signal.path in indexed:
                    duplicates.append(signal.path)
                indexed[signal.path] = signal
        return CatalogAggregate(signals=sorted(indexed.values(), key=lambda signal: signal.path), duplicates=sorted(set(duplicates)))

    def _load_file(self, path: Path) -> list[CatalogSignal]:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CatalogLoadError(f"Unable to read catalog '{path}': {exc}") from exc
        if raw is None:
            return []
        if not isinstance(raw, dict):
            raise CatalogLoadError(f"Catalog '{path}' must contain a YAML mapping.")
        raw_signals = raw.get("signals", [])
        if not isinstance(raw_signals, list):
            raise CatalogLoadError(f"Catalog '{path}' field 'signals' must be a list.")
        owner = _string(raw.get("owner") or raw.get("team") or _default_owner(path))
        catalog_since = _optional_string(raw.get("since") or raw.get("version"))
        results: list[CatalogSignal] = []
        for index, item in enumerate(raw_signals):
            if not isinstance(item, dict):
                raise CatalogLoadError(f"Catalog '{path}' signal at index {index} must be a mapping.")
            parent = _string(item.get("parent"))
            name = _string(item.get("name"))
            if not parent or not name:
                raise CatalogLoadError(f"Catalog '{path}' signal at index {index} requires parent and name.")
            results.append(CatalogSignal(
                path=f"{parent}.{name}", name=name, parent=parent,
                datatype=_optional_string(item.get("datatype")), description=_string(item.get("description")),
                unit=_optional_string(item.get("unit")), writable=bool(item.get("writable", False)),
                minimum=_optional_float(item.get("minimum")), maximum=_optional_float(item.get("maximum")),
                allowed=_optional_string_list(item.get("allowed")), owner=_string(item.get("owner") or owner),
                since=_optional_string(item.get("since") or catalog_since), source=path.name,
            ))
        return results


def _serialise_tree(node: dict[str, Any]) -> dict[str, Any]:
    result = dict(node)
    children = result.pop("children", {})
    result["children"] = [_serialise_tree(child) for _, child in sorted(children.items())]
    return result


def _default_owner(path: Path) -> str:
    stem = path.stem.replace("signals-", "")
    return f"{stem.replace('-', ' ').title()} Team"


def _string(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _optional_string(value: object) -> str | None:
    result = _string(value)
    return result or None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise CatalogLoadError("Signal minimum/maximum must be numeric.")
    if isinstance(value, (int, float)):
        return float(value)
    raise CatalogLoadError("Signal minimum/maximum must be numeric.")


def _optional_string_list(value: object) -> list[str] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise CatalogLoadError("Signal allowed values must be a list of strings.")
    return value
