import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import typer

from vssctl.commands.build import (
    parse_version_tuple,
    get_vss_version,
    check_engine_running,
    resolve_engine,
    find_latest_vss_file,
    find_build_context,
    run,
)


def test_parse_version_tuple():
    assert parse_version_tuple("6.0") == (6, 0)
    assert parse_version_tuple("3.1.1") == (3, 1, 1)
    assert parse_version_tuple("invalid") == (0,)


def test_get_vss_version():
    assert get_vss_version(Path("vss_release_6.0.json")) == "6.0"
    assert get_vss_version(Path("vss_release_3.1.1.json")) == "3.1.1"
    assert get_vss_version(Path("random_name_1.2.3.json")) == "1.2.3"
    assert get_vss_version(Path("no_version.json")) == "latest"


@patch("shutil.which")
@patch("subprocess.run")
def test_check_engine_running(mock_run, mock_which):
    # Case 1: not installed
    mock_which.return_value = None
    assert not check_engine_running("podman")

    # Case 2: installed but error
    mock_which.return_value = "/usr/bin/podman"
    mock_run.side_effect = Exception("error")
    assert not check_engine_running("podman")

    # Case 3: installed and running
    mock_run.side_effect = None
    mock_run.return_value = MagicMock(returncode=0)
    assert check_engine_running("podman")

    # Case 4: installed but exit code != 0
    mock_run.return_value = MagicMock(returncode=1)
    assert not check_engine_running("podman")


@patch("vssctl.commands.build.check_engine_running")
@patch("shutil.which")
def test_resolve_engine(mock_which, mock_check):
    # Case auto: podman running
    mock_check.side_effect = lambda x: x == "podman"
    assert resolve_engine("auto") == "podman"

    # Case auto: podman not running, docker running
    mock_check.side_effect = lambda x: x == "docker"
    assert resolve_engine("auto") == "docker"

    # Case auto: neither running
    mock_check.side_effect = lambda x: False
    with pytest.raises(typer.Exit):
        resolve_engine("auto")

    # Case explicit: installed and running
    mock_which.return_value = "/usr/bin/docker"
    mock_check.side_effect = lambda x: x == "docker"
    assert resolve_engine("docker") == "docker"

    # Case explicit: not installed
    mock_which.return_value = None
    with pytest.raises(typer.Exit):
        resolve_engine("docker")


def test_find_build_context(tmp_path):
    # Case 1: directly in folder
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    (dir1 / "Cargo.toml").touch()
    (dir1 / "databroker").mkdir()
    assert find_build_context(dir1) == dir1

    # Case 2: in sub-folder kuksa-databroker
    dir2 = tmp_path / "dir2"
    dir2.mkdir()
    sub_dir = dir2 / "kuksa-databroker"
    sub_dir.mkdir()
    (sub_dir / "Cargo.toml").touch()
    assert find_build_context(dir2) == sub_dir

    # Case 3: not found
    dir3 = tmp_path / "dir3"
    dir3.mkdir()
    with pytest.raises(typer.Exit):
        find_build_context(dir3)


def test_find_latest_vss_file(tmp_path, monkeypatch):
    generated_dir = tmp_path / "generated"
    json_tree_dir = tmp_path / "generated" / "json_tree"
    json_tree_dir.mkdir(parents=True)

    monkeypatch.setattr("vssctl.core.paths.GENERATED_DIR", generated_dir)
    monkeypatch.setattr("vssctl.core.paths.JSON_TREE_DIR", json_tree_dir)

    # Empty dirs
    with pytest.raises(typer.Exit):
        find_latest_vss_file()

    # Create file in json_tree_dir
    (json_tree_dir / "vss_release_5.1.json").touch()
    assert find_latest_vss_file() == json_tree_dir / "vss_release_5.1.json"

    # Create newer file in generated_dir
    (generated_dir / "vss_release_6.0.json").touch()
    assert find_latest_vss_file() == generated_dir / "vss_release_6.0.json"

    # Create file with sub-minor version
    (json_tree_dir / "vss_release_6.1.2.json").touch()
    assert find_latest_vss_file() == json_tree_dir / "vss_release_6.1.2.json"


@patch("platform.machine", return_value="amd64")
@patch("vssctl.commands.build.resolve_engine")
@patch("vssctl.commands.build.find_build_context")
@patch("vssctl.commands.build.find_latest_vss_file")
@patch("shutil.copy2")
@patch("subprocess.Popen")
def test_run_command_flow(mock_popen, mock_copy, mock_find_latest, mock_context, mock_resolve, mock_machine, tmp_path):
    # Setup mock returns
    mock_resolve.return_value = "podman"

    build_dir = tmp_path / "databroker"
    build_dir.mkdir()
    (build_dir / "Cargo.toml").touch()
    mock_context.return_value = build_dir

    vss_file = tmp_path / "vss_release_6.0.json"
    vss_file.touch()
    mock_find_latest.return_value = vss_file

    # Popen mock
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = ["Step 1/10...", "Step 2/10...", "Successfully built image"]
    mock_popen.return_value = mock_process

    # Call run with auto options
    run(
        vss_file=vss_file,
        tag="custom:tag",
        engine="auto",
        databroker_dir=build_dir,
        no_cache=True,
    )

    # Verify copy occurred
    temp_vss = build_dir / "vss_release.json"
    mock_copy.assert_called_once_with(vss_file, temp_vss)

    # Verify popen arguments
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    cmd_args = args[0]
    assert cmd_args[:6] == ["podman", "build", "-f", "Dockerfile.vssctl", "-t", "custom:tag"]
    assert "--no-cache" in cmd_args
    assert cmd_args[-1] == "."
    assert kwargs["cwd"] == str(build_dir)


def test_resolve_engine_rejects_unsupported_choice():
    with pytest.raises(typer.Exit) as exc_info:
        resolve_engine("containerd")
    assert exc_info.value.exit_code == 1


@patch("platform.machine", return_value="x86_64")
@patch("vssctl.commands.build.resolve_engine", return_value="docker")
@patch("subprocess.Popen")
def test_build_fast_path_uses_prebuilt_binary_and_cleans_up(mock_popen, mock_resolve, mock_machine, tmp_path):
    build_dir = tmp_path / "databroker"
    (build_dir / "databroker").mkdir(parents=True)
    (build_dir / "Cargo.toml").touch()
    binary = build_dir / "dist" / "amd64" / "databroker"
    binary.parent.mkdir(parents=True)
    binary.touch()
    vss_file = tmp_path / "vss_release_6.0.json"
    vss_file.write_text("{}", encoding="utf-8")

    captured = {}

    def capture_build(*args, **kwargs):
        captured["dockerfile"] = (build_dir / "Dockerfile.vssctl").read_text(encoding="utf-8")
        process = MagicMock(returncode=0, stdout=[])
        return process

    mock_popen.side_effect = capture_build

    run(vss_file=vss_file, engine="docker", databroker_dir=build_dir)

    assert "COPY dist/amd64/databroker /app/databroker" in captured["dockerfile"]
    assert "cargo build" not in captured["dockerfile"]
    assert not (build_dir / "Dockerfile.vssctl").exists()
    assert not (build_dir / "vss_release.json").exists()


@patch("vssctl.commands.build.resolve_engine", return_value="docker")
@patch("subprocess.Popen")
def test_failed_build_cleans_temporary_files(mock_popen, mock_resolve, tmp_path):
    build_dir = tmp_path / "databroker"
    (build_dir / "databroker").mkdir(parents=True)
    (build_dir / "Cargo.toml").touch()
    vss_file = tmp_path / "vss_release_6.0.json"
    vss_file.write_text("{}", encoding="utf-8")
    mock_popen.return_value = MagicMock(returncode=9, stdout=["failed"])

    with pytest.raises(typer.Exit) as exc_info:
        run(vss_file=vss_file, engine="docker", databroker_dir=build_dir)

    assert exc_info.value.exit_code == 1
    assert not (build_dir / "Dockerfile.vssctl").exists()
    assert not (build_dir / "vss_release.json").exists()


@patch("vssctl.commands.build.resolve_engine", return_value="docker")
@patch("subprocess.Popen")
def test_build_restores_windows_git_symlink_file(mock_popen, mock_resolve, tmp_path):
    build_dir = tmp_path / "databroker"
    (build_dir / "databroker").mkdir(parents=True)
    (build_dir / "Cargo.toml").touch()
    (build_dir / "proto").mkdir()
    (build_dir / "proto" / "schema.proto").write_text("syntax = 'proto3';", encoding="utf-8")
    symlink_file = build_dir / "databroker-proto" / "proto"
    symlink_file.parent.mkdir()
    symlink_file.write_text("../proto/", encoding="utf-8")
    vss_file = tmp_path / "vss_release_6.0.json"
    vss_file.write_text("{}", encoding="utf-8")
    mock_popen.return_value = MagicMock(returncode=0, stdout=[])

    run(vss_file=vss_file, engine="docker", databroker_dir=build_dir)

    assert symlink_file.is_file()
    assert symlink_file.read_text(encoding="utf-8") == "../proto/"
