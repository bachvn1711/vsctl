import pytest
import subprocess
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from vssctl.core.compiler import Compiler
from vssctl.core import paths
from vssctl.core.models import Catalog, Signal

def test_prepare_environment(tmp_path, monkeypatch):
    # Mock paths
    merged_dir = tmp_path / "merged"
    team_base = tmp_path / "team_base"
    company_vspec = tmp_path / "company.vspec"
    
    monkeypatch.setattr(paths, "MERGED_DIR", merged_dir)
    monkeypatch.setattr(paths, "TEAM_VSS_BASE", team_base)
    monkeypatch.setattr(paths, "COMPANY_VSPEC", company_vspec)
    
    # Create mock environment
    team_base.mkdir(parents=True)
    (team_base / "Vehicle.vspec").write_text("test")
    company_vspec.write_text("company")
    
    compiler = Compiler()
    compiler.prepare_environment()
    
    assert merged_dir.exists()
    assert (merged_dir / "Vehicle.vspec").exists()
    assert (merged_dir / "company.vspec").exists()

@patch("subprocess.run")
def test_compile(mock_run, tmp_path, monkeypatch):
    merged_dir = tmp_path / "merged"
    metadata_json = tmp_path / "vss.json"
    
    monkeypatch.setattr(paths, "MERGED_DIR", merged_dir)
    monkeypatch.setattr(paths, "METADATA_JSON", metadata_json)
    
    merged_dir.mkdir(parents=True)
    (merged_dir / "company.vspec").write_text("company")
    
    compiler = Compiler()
    compiler.compile()
    
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    
    assert any("vspec" in arg for arg in args)
    assert "export" in args
    assert "json" in args
    assert "-I" in args
    assert str(merged_dir) in args
    assert "-s" in args
    assert str(merged_dir / "company.vspec") in args
    assert "-o" in args
    assert str(metadata_json) in args


def test_compile_requires_at_least_one_vspec(tmp_path, monkeypatch):
    merged_dir = tmp_path / "merged"
    merged_dir.mkdir()
    monkeypatch.setattr(paths, "MERGED_DIR", merged_dir)

    with pytest.raises(RuntimeError, match="No .vspec files found"):
        Compiler().compile(tmp_path / "output.json")


@patch("subprocess.run")
def test_compile_reports_exporter_error(mock_run, tmp_path, monkeypatch):
    merged_dir = tmp_path / "merged"
    merged_dir.mkdir()
    (merged_dir / "company.vspec").write_text("company", encoding="utf-8")
    monkeypatch.setattr(paths, "MERGED_DIR", merged_dir)
    mock_run.side_effect = subprocess.CalledProcessError(
        2,
        ["vspec"],
        stderr="invalid specification",
    )

    with pytest.raises(RuntimeError, match="invalid specification"):
        Compiler().compile(tmp_path / "output.json")

def test_sync_all_json_versions(tmp_path, monkeypatch):
    templates_dir = tmp_path / "templates"
    json_tree_dir = tmp_path / "json_tree"
    
    monkeypatch.setattr(paths, "VSS_CORE_TEMPLATES", templates_dir)
    monkeypatch.setattr(paths, "JSON_TREE_DIR", json_tree_dir)
    
    templates_dir.mkdir(parents=True)
    
    # Create dummy VSS release templates
    release_20 = {
        "Vehicle": {
            "children": {
                "ADAS": {
                    "children": {},
                    "type": "branch",
                    "description": "ADAS branch"
                }
            },
            "type": "branch"
        }
    }
    
    release_60 = {
        "Vehicle": {
            "children": {
                "ADAS": {
                    "children": {},
                    "type": "branch",
                    "description": "ADAS branch"
                }
            },
            "type": "branch"
        }
    }
    
    with open(templates_dir / "vss_release_2.0.json", "w") as f:
        json.dump(release_20, f)
    with open(templates_dir / "vss_release_6.0.json", "w") as f:
        json.dump(release_60, f)

    # Simulate a previously modified target file containing OldCustom
    target_60 = {
        "Vehicle": {
            "children": {
                "ADAS": {
                    "children": {
                        "OldCustom": {
                            "datatype": "boolean",
                            "description": "Old custom signal",
                            "type": "sensor"
                        }
                    },
                    "type": "branch",
                    "description": "ADAS branch"
                }
            },
            "type": "branch"
        }
    }
    json_tree_dir.mkdir(parents=True)
    with open(json_tree_dir / "vss_release_6.0.json", "w") as f:
        json.dump(target_60, f)
        
    # Active Catalog has Speed (new), and OldCustom is removed
    catalog = Catalog(signals=[
        Signal(
            parent="Vehicle.ADAS",
            name="Speed",
            datatype="float",
            description="Custom speed",
            unit="km/h",
            writable=True,
            minimum=0.0,
            maximum=250.0
        )
    ])
    
    compiler = Compiler()
    compiler.sync_all_json_versions(catalog)
    
    assert (json_tree_dir / "vss_release_2.0.json").exists()
    assert (json_tree_dir / "vss_release_6.0.json").exists()
    
    with open(json_tree_dir / "vss_release_2.0.json", "r") as f:
        tree_20 = json.load(f)
    with open(json_tree_dir / "vss_release_6.0.json", "r") as f:
        tree_60 = json.load(f)
        
    # Check that Speed was added in both
    speed_node_20 = tree_20["Vehicle"]["children"]["ADAS"]["children"]["Speed"]
    assert speed_node_20["type"] == "actuator"
    assert speed_node_20["datatype"] == "float"
    assert speed_node_20["unit"] == "km/h"
    assert speed_node_20["min"] == 0.0
    assert speed_node_20["max"] == 250.0
    
    speed_node_60 = tree_60["Vehicle"]["children"]["ADAS"]["children"]["Speed"]
    assert speed_node_60["type"] == "actuator"
    
    # OldCustom should be removed from vss_release_6.0.json
    assert "OldCustom" not in tree_60["Vehicle"]["children"]["ADAS"]["children"]
