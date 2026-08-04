from __future__ import annotations

import json
from pathlib import Path

from vssctl.core.models import Signal
from vssctl.core.paths import JSON_TREE_DIR, VSS_CORE_TEMPLATES


def baseline_signal_paths(version: str = "6.0") -> set[str]:
    """Return paths defined by the canonical template VSS JSON."""
    filename = f"vss_release_{version}.json"
    candidates = [VSS_CORE_TEMPLATES / filename]
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        locations = ", ".join(str(candidate) for candidate in candidates)
        raise FileNotFoundError(f"Baseline VSS JSON not found in: {locations}")
    return _paths_from_json(path)


def output_signal_paths(version: str = "6.0") -> set[str]:
    """Return paths from the generated synchronized JSON tree."""
    path = JSON_TREE_DIR / f"vss_release_{version}.json"
    if not path.is_file():
        return set()
    return _paths_from_json(path)


def custom_signals(signals: list[Signal], baseline_paths: set[str]) -> list[Signal]:
    """Return catalog entries whose full paths are absent from the baseline."""
    return [signal for signal in signals if _signal_path(signal) not in baseline_paths]


def _signal_path(signal: Signal) -> str:
    return f"{signal.parent}.{signal.name}"


def _paths_from_json(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"VSS JSON must contain an object: {path}")
    result: set[str] = set()
    _collect_paths(data, "", result)
    return result


def _collect_paths(node: object, prefix: str, result: set[str]) -> None:
    if not isinstance(node, dict):
        return
    for name, value in node.items():
        if name in {"children", "description", "type", "datatype", "unit", "writable", "minimum", "maximum", "allowed", "comment", "uuid"}:
            continue
        if not isinstance(value, dict):
            continue
        current = f"{prefix}.{name}" if prefix else name
        result.add(current)
        children = value.get("children")
        if isinstance(children, dict):
            _collect_paths(children, current, result)
