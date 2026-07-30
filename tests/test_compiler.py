import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
from vssctl.core.compiler import Compiler
from vssctl.core import paths

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
    
    assert args[0] == "vspec2json"
    assert "-I" in args
    assert str(merged_dir) in args
    assert str(merged_dir / "company.vspec") in args
    assert str(metadata_json) in args
