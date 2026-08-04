from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vssctl.cli import app
from vssctl.config import settings
from vssctl.core.models import Catalog, Signal
from vssctl.core.storage import Storage


runner = CliRunner()


def _save_catalogs(base: list[Signal] | None = None, custom: list[Signal] | None = None) -> None:
    storage = Storage()
    storage.save_base(Catalog(signals=base or []))
    storage.save_custom(Catalog(signals=custom or []))


def test_root_help_and_no_args_show_command_contract():
    for arguments, expected_code in (([], 2), (["--help"], 0)):
        result = runner.invoke(app, arguments)
        assert result.exit_code == expected_code
        assert "Vehicle Signal Specification Management Tool" in result.output
        for command in ("doctor", "signal", "validate", "generate", "build", "publish", "pipeline", "completion", "browse"):
            assert command in result.output


def test_global_config_and_logging_flags(tmp_path):
    config = tmp_path / ".vssctl.yaml"
    config.write_text(
        "workspace:\n  databroker_path: custom/db\n  output_dir: custom/out\n"
        "defaults:\n  engine: docker\n  ghcr_org: test-org\n  vss_version: '5.1'\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["--config", str(config), "--verbose", "doctor"])

    assert result.exit_code == 0
    assert settings.databroker_path == "custom/db"
    assert settings.output_dir == "custom/out"
    assert settings.engine == "docker"
    assert settings.ghcr_org == "test-org"
    assert settings.vss_version == "5.1"
    assert settings.verbose is True
    assert settings.quiet is False

    result = runner.invoke(app, ["--quiet", "doctor"])
    assert result.exit_code == 0
    assert settings.quiet is True


def test_doctor_reports_platform_and_ok():
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "vssctl" in result.output
    assert "OK" in result.output


def test_signal_add_retries_invalid_node_type_and_saves(isolated_workspace):
    result = runner.invoke(
        app,
        ["signal", "add"],
        input="invalid\nsignal\nVehicle.ADAS\nSpeed\nVehicle speed\nfloat\nkm/h\n",
    )

    assert result.exit_code == 0
    assert "Invalid choice" in result.output
    assert "Success: Node added" in result.output
    saved = Storage().load_custom().signals
    assert [(signal.parent, signal.name, signal.unit) for signal in saved] == [
        ("Vehicle.ADAS", "Speed", "km/h")
    ]


def test_signal_add_validation_error_returns_one(isolated_workspace):
    result = runner.invoke(
        app,
        ["signal", "add"],
        input="signal\nVehicle.ADAS\nspeed\nVehicle speed\nfloat\n\n",
    )
    assert result.exit_code == 1
    assert "Error:" in result.output
    assert Storage().load_custom().signals == []


def test_signal_list_and_search_separate_base_and_custom(isolated_workspace):
    _save_catalogs(
        base=[Signal(parent="Vehicle.ADAS", name="Standard", datatype="float", description="Base")],
        custom=[Signal(parent="Vehicle.ADAS", name="CustomSpeed", datatype="float", description="Custom speed")],
    )
    baseline_json = {
        "Vehicle": {
            "type": "branch",
            "children": {"ADAS": {"type": "branch", "children": {"Standard": {"type": "sensor"}}}},
        }
    }
    baseline_path = isolated_workspace.templates_dir / "vss-core" / "vss_release_6.0.json"
    baseline_path.write_text(json.dumps(baseline_json), encoding="utf-8")

    listed = runner.invoke(app, ["signal", "list"])
    searched = runner.invoke(app, ["signal", "search", "speed"])

    assert listed.exit_code == 0
    assert "Base signals" in listed.output
    assert "Vehicle.ADAS.Standard" in listed.output
    assert "Custom signals" in listed.output
    assert "Vehicle.ADAS.CustomSpeed" in listed.output
    assert searched.exit_code == 0
    assert "Vehicle.ADAS.CustomSpeed" in searched.output


def test_signal_remove_branch_recursively_and_missing_path(isolated_workspace):
    _save_catalogs(custom=[
        Signal(parent="Vehicle.ADAS", name="Custom", datatype=None, description="Branch"),
        Signal(parent="Vehicle.ADAS.Custom", name="Speed", datatype="float", description="Speed"),
        Signal(parent="Vehicle.Body", name="Keep", datatype="boolean", description="Keep"),
    ])

    removed = runner.invoke(app, ["signal", "remove", "Vehicle.ADAS.Custom"])
    assert removed.exit_code == 0
    assert "1 child signal(s)" in removed.output
    assert [signal.name for signal in Storage().load_custom().signals] == ["Keep"]

    missing = runner.invoke(app, ["signal", "remove", "Vehicle.ADAS.Unknown"])
    assert missing.exit_code == 0
    assert "not found" in missing.output

    no_target = runner.invoke(app, ["signal", "remove"])
    assert no_target.exit_code == 1
    assert "Provide a path or use --all" in no_target.output


def test_signal_remove_all_preserves_base_catalog(isolated_workspace):
    base = Signal(parent="Vehicle.ADAS", name="Base", datatype=None, description="Base")
    custom = Signal(parent="Vehicle.ADAS", name="Custom", datatype=None, description="Custom")
    _save_catalogs(base=[base], custom=[custom])

    result = runner.invoke(app, ["signal", "remove", "--all"])

    assert result.exit_code == 0
    assert Storage().load_custom().signals == []
    assert [signal.name for signal in Storage().load_base().signals] == ["Base"]


def test_signal_update_imports_baseline_branches_and_preserves_custom(isolated_workspace):
    custom = Signal(parent="Vehicle.ADAS", name="CustomSpeed", datatype="float", description="Custom")
    _save_catalogs(custom=[custom])
    baseline_json = {
        "Vehicle": {
            "type": "branch",
            "children": {
                "ADAS": {
                    "type": "branch",
                    "description": "ADAS",
                    "children": {"Feature": {"type": "branch", "description": "Feature", "children": {}}},
                }
            },
        }
    }
    baseline_path = isolated_workspace.templates_dir / "vss-core" / "vss_release_6.0.json"
    baseline_path.write_text(json.dumps(baseline_json), encoding="utf-8")

    result = runner.invoke(app, ["signal", "update", "--version", "6.0"])

    assert result.exit_code == 0
    assert {signal.name for signal in Storage().load_base().signals} == {"ADAS", "Feature"}
    assert [signal.name for signal in Storage().load_custom().signals] == ["CustomSpeed"]


def test_validate_cli_success_empty_and_failure(isolated_workspace):
    empty = runner.invoke(app, ["validate"])
    assert empty.exit_code == 0
    assert "Catalog is empty" in empty.output

    _save_catalogs(custom=[Signal(parent="Vehicle.ADAS", name="Speed", datatype="float", description="Speed")])
    valid = runner.invoke(app, ["validate"])
    assert valid.exit_code == 0
    assert "Catalog is valid" in valid.output

    _save_catalogs(custom=[Signal(parent="Vehicle.ADAS", name="speed", datatype="float", description="Speed")])
    invalid = runner.invoke(app, ["validate"])
    assert invalid.exit_code == 1
    assert "Validation failed" in invalid.output


@patch("vssctl.commands.generate.Compiler")
@patch("vssctl.commands.generate.Generator")
def test_generate_cli_specific_version_and_compiler_failure(mock_generator, mock_compiler, isolated_workspace):
    _save_catalogs(custom=[Signal(parent="Vehicle.ADAS", name="Speed", datatype="float", description="Speed")])

    success = runner.invoke(app, ["generate", "--version", "6.0"])
    assert success.exit_code == 0
    mock_compiler.return_value.compile.assert_called_once_with(
        isolated_workspace.generated_dir / "json_tree" / "vss_release_6.0.json"
    )

    mock_compiler.return_value.compile.side_effect = RuntimeError("compiler unavailable")
    failure = runner.invoke(app, ["generate", "--version", "6.0"])
    assert failure.exit_code == 1
    assert "compiler unavailable" in failure.output


def test_completion_rejects_unknown_shell():
    result = runner.invoke(app, ["completion", "powershell"])
    assert result.exit_code == 1
    assert "Unsupported shell" in result.output


def test_browse_rejects_non_interactive_terminal(isolated_workspace):
    result = runner.invoke(app, ["browse", "--source", "custom"])
    assert result.exit_code == 1
    assert "requires an interactive terminal" in result.output
