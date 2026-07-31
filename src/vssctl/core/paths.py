from pathlib import Path
import os
from typing import Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parents[3]

WORKSPACE = PROJECT_ROOT / "workspace"

CATALOG_DIR = WORKSPACE / "catalog"
GENERATED_DIR = WORKSPACE / "generated"
BUILD_DIR = WORKSPACE / "build"
MERGED_DIR = GENERATED_DIR / "merged"
TEAM_VSS_BASE = WORKSPACE / "templates" / "spec"
VSS_CORE_TEMPLATES = WORKSPACE / "templates" / "vss-core"
JSON_TREE_DIR = GENERATED_DIR / "json_tree"

SIGNALS_BASE_YAML = CATALOG_DIR / "signals-base.yaml"
SIGNALS_CUSTOM_YAML = CATALOG_DIR / "signals-custom.yaml"
SIGNALS_YAML = SIGNALS_CUSTOM_YAML

TREE_JSON = GENERATED_DIR / "tree.json"
COMPANY_VSPEC = GENERATED_DIR / "company.vspec"
METADATA_JSON = GENERATED_DIR / "vss_release_6.0.json"


def resolve_path_gracefully(path_input: Optional[Union[Path, str]]) -> Optional[Path]:
    """
    Resolves absolute or relative paths gracefully.
    If the path does not exist, checks relative to PROJECT_ROOT or os.getcwd() (CWD).
    """
    if path_input is None:
        return None
        
    p = Path(path_input)
    
    # 1. Check if it exists directly (absolute or relative to current directory)
    if p.exists():
        return p.resolve()
        
    # 2. If it is relative, check if it exists relative to PROJECT_ROOT or CWD
    if not p.is_absolute():
        root_p = PROJECT_ROOT / p
        if root_p.exists():
            return root_p.resolve()
        cwd_p = Path(os.getcwd()) / p
        if cwd_p.exists():
            return cwd_p.resolve()
            
    # 3. If it is absolute but does not exist, it might have been configured for another system.
    # Try to find a subpath (from right to left) that exists relative to PROJECT_ROOT or CWD.
    if p.is_absolute():
        parts = p.parts
        for i in range(len(parts)):
            subpath = Path(*parts[i:])
            # Try PROJECT_ROOT
            root_p = PROJECT_ROOT / subpath
            if root_p.exists():
                return root_p.resolve()
            # Try CWD
            cwd_p = Path(os.getcwd()) / subpath
            if cwd_p.exists():
                return cwd_p.resolve()
                
    # 4. Fallback: resolve relative to CWD
    if not p.is_absolute():
        return (Path(os.getcwd()) / p).resolve()
    else:
        # If absolute, fallback to filename in CWD or just return the resolved path
        fallback = Path(os.getcwd()) / p.name
        if fallback.exists():
            return fallback.resolve()
        return p.resolve()