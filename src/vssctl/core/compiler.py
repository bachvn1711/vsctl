import subprocess
import shutil
import sys
from pathlib import Path

from vssctl.core import paths


class Compiler:
    """
    Handles environment preparation and invoking the official VSS compiler.
    """

    def prepare_environment(self) -> None:
        """
        Creates workspace/generated/merged/ and copies all contents from TEAM_VSS_BASE to it.
        Then copies generated company.vspec into the merged directory.
        """
        # Clean or create merged directory
        if paths.MERGED_DIR.exists():
            shutil.rmtree(paths.MERGED_DIR)
        
        paths.MERGED_DIR.mkdir(parents=True, exist_ok=True)

        # Copy official VSS files
        if paths.TEAM_VSS_BASE.exists() and paths.TEAM_VSS_BASE.is_dir():
            for item in paths.TEAM_VSS_BASE.iterdir():
                if item.is_dir():
                    shutil.copytree(item, paths.MERGED_DIR / item.name)
                else:
                    shutil.copy2(item, paths.MERGED_DIR / item.name)

        # Copy generated company.vspec
        if paths.COMPANY_VSPEC.exists():
            shutil.copy2(paths.COMPANY_VSPEC, paths.MERGED_DIR / paths.COMPANY_VSPEC.name)

    def compile(self) -> None:
        """
        Invokes the official vspec compiler to generate the JSON.
        """
        # Look for VehicleSignalSpecification.vspec or Vehicle.vspec
        merged_vehicle_vspec = paths.MERGED_DIR / "VehicleSignalSpecification.vspec"
        if not merged_vehicle_vspec.exists():
            merged_vehicle_vspec = paths.MERGED_DIR / "Vehicle.vspec"
            
        merged_company_vspec = paths.MERGED_DIR / "company.vspec"

        if not merged_vehicle_vspec.exists() and not merged_company_vspec.exists():
            raise RuntimeError("No .vspec files found to compile.")

        # Determine path to the vspec executable
        executable_dir = Path(sys.executable).parent
        vspec_bin = "vspec.exe" if sys.platform == "win32" else "vspec"
        vspec_path = executable_dir / vspec_bin

        if vspec_path.exists():
            cmd = [str(vspec_path)]
        else:
            cmd = ["vspec"]

        cmd.extend(["export", "json"])

        # Include directory
        cmd.extend(["-I", str(paths.MERGED_DIR)])

        # Main vspec file is the vehicle spec if it exists, otherwise company.vspec
        if merged_vehicle_vspec.exists():
            cmd.extend(["-s", str(merged_vehicle_vspec)])
            # company.vspec acts as an overlay
            if merged_company_vspec.exists():
                cmd.extend(["-l", str(merged_company_vspec)])
        else:
            cmd.extend(["-s", str(merged_company_vspec)])

        # Ensure output directory exists
        paths.METADATA_JSON.parent.mkdir(parents=True, exist_ok=True)
        cmd.extend(["-o", str(paths.METADATA_JSON)])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr or e.stdout or str(e)
            raise RuntimeError(f"VSS compiler failed: {err_msg}")

    def sync_all_json_versions(self, catalog) -> None:
        """
        Synchronizes catalog custom signals across all VSS release JSON files in json_tree/.
        """
        import json

        # Ensure output directory exists
        paths.JSON_TREE_DIR.mkdir(parents=True, exist_ok=True)

        if not paths.VSS_CORE_TEMPLATES.exists() or not paths.VSS_CORE_TEMPLATES.is_dir():
            raise RuntimeError(f"VSS core templates directory does not exist: {paths.VSS_CORE_TEMPLATES}")

        # Compute active custom paths from catalog
        active_custom_paths = set()
        for signal in catalog.signals:
            sig_path = f"{signal.parent}.{signal.name}"
            active_custom_paths.add(sig_path)
            # Add intermediate custom branches
            parts = signal.parent.split(".")
            for i in range(1, len(parts)):
                branch_path = ".".join(parts[:i+1])
                active_custom_paths.add(branch_path)

        # For each JSON file in the templates directory
        for item in paths.VSS_CORE_TEMPLATES.iterdir():
            if item.is_file() and item.name.endswith(".json") and item.name.startswith("vss_release_"):
                target_file = paths.JSON_TREE_DIR / item.name
                
                # Copy template if target does not exist
                if not target_file.exists():
                    shutil.copy2(item, target_file)

                # Load template data (to identify baseline nodes) and target data
                with open(item, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                
                with open(target_file, "r", encoding="utf-8") as f:
                    target_data = json.load(f)

                # Get all paths in template (official paths) and target
                template_paths = self._get_all_paths(template_data)
                target_paths = self._get_all_paths(target_data)

                # Remove any custom nodes in target that are not active in catalog
                for path in list(target_paths.keys()):
                    if path not in template_paths:  # It is a custom node
                        if path not in active_custom_paths:
                            self._remove_node(target_data, path)

                # Add or update custom signals/branches from the catalog
                for signal in catalog.signals:
                    # First ensure intermediate branches are present and updated
                    parts = signal.parent.split(".")
                    for i in range(1, len(parts)):
                        branch_path = ".".join(parts[:i+1])
                        if branch_path not in template_paths:
                            branch_dict = {
                                "type": "branch",
                                "description": f"Custom branch {parts[i]}"
                            }
                            self._add_or_update_node(target_data, branch_path, branch_dict)

                    # Now add/update the signal itself
                    sig_path = f"{signal.parent}.{signal.name}"
                    if signal.datatype is None:
                        sig_dict = {
                            "type": "branch",
                            "description": signal.description
                        }
                    else:
                        sig_dict = {
                            "type": "actuator" if getattr(signal, "writable", False) else "sensor",
                            "datatype": signal.datatype,
                            "description": signal.description
                        }
                        if getattr(signal, "unit", None):
                            sig_dict["unit"] = signal.unit
                        if getattr(signal, "minimum", None) is not None:
                            sig_dict["min"] = signal.minimum
                        if getattr(signal, "maximum", None) is not None:
                            sig_dict["max"] = signal.maximum

                    self._add_or_update_node(target_data, sig_path, sig_dict)

                # Save updated target JSON
                with open(target_file, "w", encoding="utf-8") as f:
                    json.dump(target_data, f, indent=2, sort_keys=True)

    def _get_all_paths(self, tree) -> dict:
        paths_map = {}
        def traverse(node, path):
            paths_map[path] = node
            if isinstance(node, dict) and "children" in node:
                for name, child in node["children"].items():
                    traverse(child, f"{path}.{name}")
        for root_name, root_node in tree.items():
            traverse(root_node, root_name)
        return paths_map

    def _remove_node(self, tree, path) -> None:
        parts = path.split(".")
        if not parts:
            return
        if len(parts) == 1:
            if parts[0] in tree:
                del tree[parts[0]]
            return
        
        current = tree.get(parts[0])
        for part in parts[1:-1]:
            if current is not None and "children" in current and part in current["children"]:
                current = current["children"][part]
            else:
                return
        if current is not None and "children" in current and parts[-1] in current["children"]:
            del current["children"][parts[-1]]

    def _add_or_update_node(self, tree, path, node_dict) -> None:
        parts = path.split(".")
        if not parts:
            return
        current = tree
        if parts[0] not in current:
            current[parts[0]] = {"children": {}}
        current = current[parts[0]]
        
        for part in parts[1:-1]:
            if "children" not in current:
                current["children"] = {}
            if part not in current["children"]:
                current["children"][part] = {"type": "branch", "description": f"Custom branch {part}", "children": {}}
            current = current["children"][part]
        
        if "children" not in current:
            current["children"] = {}
        
        last_part = parts[-1]
        if last_part not in current["children"]:
            current["children"][last_part] = node_dict
        else:
            existing = current["children"][last_part]
            children_dict = existing.get("children", {})
            existing.clear()
            existing.update(node_dict)
            if children_dict:
                existing["children"] = children_dict

