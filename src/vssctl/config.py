import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml

class Config:
    def __init__(self):
        # Default workspace settings
        self.databroker_path = "workspace/databroker"
        self.output_dir = "workspace/output"
        
        # Default CLI settings
        self.engine = "auto"
        self.ghcr_org = "bachvn1711"
        self.vss_version = "6.0"
        
        # Verbosity controls
        self.verbose = False
        self.quiet = False

    def load(self, path: Optional[Path] = None):
        """
        Loads configuration from a yaml file.
        Searches path first, then project root, then $HOME/.vssctl.yaml.
        """
        search_paths = []
        if path:
            from vssctl.core.paths import resolve_path_gracefully
            resolved = resolve_path_gracefully(path)
            if resolved:
                search_paths.append(resolved)
        
        # Resolve project root relative to this file (vssctl/src/vssctl/config.py)
        # parents[2] gets the folder holding 'src' (project root)
        project_root = Path(__file__).resolve().parents[2]
        search_paths.append(project_root / ".vssctl.yaml")
        search_paths.append(Path.home() / ".vssctl.yaml")
        
        for p in search_paths:
            if p.exists() and p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        self._parse_data(data)
                        break
                except Exception:
                    pass

    def _parse_data(self, data: Dict[str, Any]):
        workspace = data.get("workspace", {})
        self.databroker_path = workspace.get("databroker_path", self.databroker_path)
        self.output_dir = workspace.get("output_dir", self.output_dir)
        
        defaults = data.get("defaults", {})
        self.engine = defaults.get("engine", self.engine)
        self.ghcr_org = defaults.get("ghcr_org", self.ghcr_org)
        self.vss_version = defaults.get("vss_version", self.vss_version)

# Global settings instance
settings = Config()
