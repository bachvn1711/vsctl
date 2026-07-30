from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

WORKSPACE = PROJECT_ROOT / "workspace"

CATALOG_DIR = WORKSPACE / "catalog"
GENERATED_DIR = WORKSPACE / "generated"
BUILD_DIR = WORKSPACE / "build"
MERGED_DIR = GENERATED_DIR / "merged"
TEAM_VSS_BASE = WORKSPACE / "templates" / "spec"
VSS_CORE_TEMPLATES = WORKSPACE / "templates" / "vss-core"
JSON_TREE_DIR = GENERATED_DIR / "json_tree"

SIGNALS_YAML = CATALOG_DIR / "signals.yaml"

TREE_JSON = GENERATED_DIR / "tree.json"
COMPANY_VSPEC = GENERATED_DIR / "company.vspec"
METADATA_JSON = GENERATED_DIR / "vss_release_6.0.json"