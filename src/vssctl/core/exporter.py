from __future__ import annotations

import json
from pathlib import Path

from vssctl.core.tree import TreeNode


class Exporter:

    def export_tree_json(
        self,
        tree: TreeNode,
        output: Path,
    ) -> None:

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open("w", encoding="utf-8") as f:

            json.dump(
                tree.to_dict(),
                f,
                indent=2,
            )

        print(f"✓ Tree exported to {output}")