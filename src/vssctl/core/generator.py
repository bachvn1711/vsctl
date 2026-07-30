import yaml
from pathlib import Path

from vssctl.core.tree import TreeNode
from vssctl.core import paths

class Generator:
    """
    Generates company.vspec based on the built tree of custom signals.
    """

    def generate(self, root: TreeNode, output_path: Path = paths.COMPANY_VSPEC) -> None:
        """
        Generate company.vspec YAML file from the custom signal tree.
        """
        vspec_data = {}

        for node in root.walk():
            # The root node "Vehicle" is assumed to be defined in the standard VSS.
            # We don't need to output it, we only output its descendants.
            if node.is_root and node.name == "Vehicle":
                continue

            node_dict = {}
            if node.is_branch:
                node_dict["type"] = "branch"
                node_dict["description"] = f"Custom branch {node.name}"
            elif node.is_signal:
                sig = node.signal
                node_dict["type"] = "actuator" if getattr(sig, "writable", False) else "sensor"
                node_dict["datatype"] = sig.datatype
                node_dict["description"] = sig.description
                
                if getattr(sig, "unit", None):
                    node_dict["unit"] = sig.unit
                if getattr(sig, "minimum", None) is not None:
                    node_dict["min"] = sig.minimum
                if getattr(sig, "maximum", None) is not None:
                    node_dict["max"] = sig.maximum
            
            vspec_data[node.path] = node_dict

        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(vspec_data, f, sort_keys=False)