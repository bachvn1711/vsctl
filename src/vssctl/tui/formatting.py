from __future__ import annotations

from vssctl.core.tree import TreeNode


def format_node_details(node: TreeNode) -> str:
    if not node.is_signal or node.signal is None:
        return f"Branch\n\nPath: {node.path}\nChildren: {len(node.children)}"

    signal = node.signal
    lines = [f"Signal\n\nPath: {node.path}", f"Datatype: {signal.datatype or '-'}", f"Unit: {signal.unit or '-'}"]
    lines.extend([f"Writable: {'yes' if signal.writable else 'no'}", f"Range: {_range(signal)}"])
    lines.append(f"\nDescription: {signal.description or '-'}")
    return "\n".join(lines)


def _range(signal: object) -> str:
    minimum = getattr(signal, "minimum", None)
    maximum = getattr(signal, "maximum", None)
    if minimum is None and maximum is None:
        return "-"
    return f"{minimum if minimum is not None else '-'} .. {maximum if maximum is not None else '-'}"
