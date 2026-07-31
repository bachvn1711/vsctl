import yaml
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import typer

from vssctl.config import settings, Config
from vssctl.commands import validate, completion, pipeline
from vssctl.core.models import Signal


def test_config_default_values():
    config = Config()
    assert config.databroker_path == "workspace/databroker"
    assert config.engine == "auto"
    assert config.ghcr_org == "bachvn1711"
    assert config.vss_version == "6.0"


def test_config_load_from_yaml(tmp_path):
    config_file = tmp_path / ".vssctl.yaml"
    config_data = {
        "workspace": {
            "databroker_path": "/custom/path",
            "output_dir": "/custom/out"
        },
        "defaults": {
            "engine": "docker",
            "ghcr_org": "test-org",
            "vss_version": "5.1"
        }
    }
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f)

    config = Config()
    config.load(config_file)
    
    assert config.databroker_path == "/custom/path"
    assert config.output_dir == "/custom/out"
    assert config.engine == "docker"
    assert config.ghcr_org == "test-org"
    assert config.vss_version == "5.1"


@patch("vssctl.commands.validate.CatalogService")
def test_validate_command_empty_catalog(mock_catalog_service):
    # Mock empty catalog
    mock_service_instance = MagicMock()
    mock_service_instance.list.return_value = []
    mock_catalog_service.return_value = mock_service_instance

    # Should complete without error (returns None)
    validate.run()


@patch("vssctl.commands.validate.CatalogService")
def test_validate_command_success(mock_catalog_service):
    # Mock valid catalog signals
    mock_service_instance = MagicMock()
    mock_service_instance.list.return_value = [
        Signal(parent="Vehicle.Cabin", name="DoorCount", datatype="uint8", description="Doors"),
        Signal(parent="Vehicle.Cabin", name="HVAC", datatype=None, description="HVAC Branch")
    ]
    mock_catalog_service.return_value = mock_service_instance

    # Should run successfully without raising Exit
    validate.run()


@patch("vssctl.commands.validate.CatalogService")
def test_validate_command_failure_duplicates(mock_catalog_service):
    # Mock duplicate signals in catalog
    mock_service_instance = MagicMock()
    mock_service_instance.list.return_value = [
        Signal(parent="Vehicle.Cabin", name="DoorCount", datatype="uint8", description="Doors"),
        Signal(parent="Vehicle.Cabin", name="DoorCount", datatype="uint8", description="Duplicate doors")
    ]
    mock_catalog_service.return_value = mock_service_instance

    # Should fail and raise typer.Exit(1)
    with pytest.raises(typer.Exit):
        validate.run()


@patch("vssctl.commands.validate.CatalogService")
def test_validate_command_failure_invalid_name(mock_catalog_service):
    mock_service_instance = MagicMock()
    mock_service_instance.list.return_value = [
        # Invalid name starts with lowercase letter
        Signal(parent="Vehicle.Cabin", name="doorCount", datatype="uint8", description="Doors")
    ]
    mock_catalog_service.return_value = mock_service_instance

    with pytest.raises(typer.Exit):
        validate.run()


@patch("subprocess.run")
def test_completion_command_generation(mock_run):
    mock_run.return_value = MagicMock(stdout="complete -o default -F _vssctl_completion vssctl", returncode=0)

    # Calling completion generator for bash
    completion.run(shell="bash")

    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    cmd = args[0]
    assert cmd[1:] == ["-m", "vssctl.cli"]
    assert kwargs["env"]["_VSSCTL_COMPLETE"] == "bash_source"


@patch("vssctl.commands.validate.run")
@patch("vssctl.commands.generate.run")
@patch("vssctl.commands.build.run")
def test_pipeline_workflow(mock_build, mock_generate, mock_validate):
    pipeline.run(
        version="6.0",
        vss_file=Path("workspace/generated/vss_release_6.0.json"),
        tag="custom-tag",
        engine="docker",
        databroker_dir=Path("custom-dir"),
        no_cache=True,
        publish=True,
        token="test_token",
        username="bachvn1711",
        remote_tag="remtag",
        skip_login=True,
    )

    mock_validate.assert_called_once()
    mock_generate.assert_called_once_with(version="6.0")
    mock_build.assert_called_once_with(
        vss_file=Path("workspace/generated/vss_release_6.0.json"),
        tag="custom-tag",
        engine="docker",
        databroker_dir=Path("custom-dir"),
        no_cache=True,
        publish=True,
        token="test_token",
        username="bachvn1711",
        remote_tag="remtag",
        skip_login=True,
    )


def test_parent_wheels_normalization():
    sig = Signal(parent="Vehicle.Chassis.Wheels", name="SteerAngle", datatype="int16", description="Angle")
    assert sig.parent == "Vehicle.Chassis.Wheel"
    
    # Test lowercase wheels
    sig2 = Signal(parent="Vehicle.wheels.FrontLeft", name="SteerAngle", datatype="int16", description="Angle")
    assert sig2.parent == "Vehicle.Wheel.FrontLeft"

    # Test normal unchanged
    sig3 = Signal(parent="Vehicle.Cabin", name="DoorCount", datatype="uint8", description="Doors")
    assert sig3.parent == "Vehicle.Cabin"


@patch("vssctl.commands.generate.CatalogService")
@patch("vssctl.commands.generate.TreeBuilder")
@patch("vssctl.commands.generate.Generator")
@patch("vssctl.commands.generate.Compiler")
def test_generate_all_versions(mock_compiler_class, mock_generator_class, mock_tree_class, mock_catalog_class, tmp_path):
    mock_catalog = MagicMock()
    mock_catalog_class.return_value.catalog = mock_catalog
    
    mock_compiler = MagicMock()
    mock_compiler_class.return_value = mock_compiler
    
    # Mock settings.output_dir to use a temp dir
    from vssctl.config import settings
    original_output_dir = settings.output_dir
    settings.output_dir = str(tmp_path)
    
    try:
        from vssctl.commands import generate
        # Run generate without arguments
        generate.run(version=None)
        
        # Verify compiler.compile was called with the default 6.0 path
        mock_compiler.compile.assert_called_once()
        # Verify sync_all_json_versions was called with catalog
        mock_compiler.sync_all_json_versions.assert_called_once_with(mock_catalog)
    finally:
        settings.output_dir = original_output_dir
