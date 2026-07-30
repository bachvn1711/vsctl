import pytest
import yaml
from pathlib import Path
from vssctl.core.tree import TreeNode
from vssctl.core.models import Signal
from vssctl.core.generator import Generator

def test_generator_creates_valid_yaml(tmp_path):
    output_path = tmp_path / "company.vspec"
    
    # Create a small tree
    root = TreeNode("Vehicle")
    branch = TreeNode("Custom")
    root.add_child(branch)
    
    sig1 = Signal(
        parent="Vehicle.Custom",
        name="Speed",
        datatype="float",
        description="Custom speed",
        unit="km/h"
    )
    node_sig1 = TreeNode("Speed", signal=sig1)
    branch.add_child(node_sig1)
    
    generator = Generator()
    generator.generate(root, output_path)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    assert "Vehicle.Custom" in data
    assert data["Vehicle.Custom"]["type"] == "branch"
    
    assert "Vehicle.Custom.Speed" in data
    assert data["Vehicle.Custom.Speed"]["type"] == "sensor"
    assert data["Vehicle.Custom.Speed"]["datatype"] == "float"
    assert data["Vehicle.Custom.Speed"]["unit"] == "km/h"
    
    # Root should be excluded
    assert "Vehicle" not in data
