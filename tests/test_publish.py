import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import typer

from vssctl.commands.publish import run_publish_flow, run
from vssctl.commands.build import run as build_run


@patch("vssctl.commands.publish.resolve_engine")
@patch("subprocess.run")
def test_publish_local_image_not_found(mock_run, mock_resolve):
    mock_resolve.return_value = "docker"
    # Inspect returns non-zero
    mock_run.return_value = MagicMock(returncode=1)

    with pytest.raises(typer.Exit):
        run_publish_flow(
            image="nonexistent:latest",
            remote_tag="latest",
            token=None,
            username="bachvn1711",
            engine="auto",
            skip_login=True,
        )


@patch("vssctl.commands.publish.resolve_engine")
@patch("subprocess.run")
@patch("subprocess.Popen")
def test_publish_tag_formatting_and_tagging(mock_popen, mock_run, mock_resolve):
    mock_resolve.return_value = "podman"
    # mock inspect check success
    mock_run.return_value = MagicMock(returncode=0)

    # mock push process
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = ["Pushing layer...", "Pushed"]
    mock_popen.return_value = mock_proc

    # Case 1: Tag only
    remote_uri = run_publish_flow(
        image="kuksa-databroker:vss-6.0",
        remote_tag="vss6.0",
        token=None,
        username="bachvn1711",
        engine="podman",
        skip_login=True,
    )
    assert remote_uri == "ghcr.io/bachvn1711/databroker:vss6.0"

    # Case 2: Full registry path
    remote_uri_full = run_publish_flow(
        image="kuksa-databroker:vss-6.0",
        remote_tag="ghcr.io/customorg/mybroker:vss-test",
        token=None,
        username="bachvn1711",
        engine="podman",
        skip_login=True,
    )
    assert remote_uri_full == "ghcr.io/customorg/mybroker:vss-test"


@patch("vssctl.commands.publish.resolve_engine")
@patch("subprocess.run")
@patch("subprocess.Popen")
@patch.dict(os.environ, {"GHCR_TOKEN": "env_token_123"}, clear=True)
def test_publish_login_flow_with_token(mock_popen, mock_run, mock_resolve):
    mock_resolve.return_value = "docker"
    # Inspect (success), Login (success), Tag (success)
    mock_run.side_effect = [
        MagicMock(returncode=0),  # inspect
        MagicMock(returncode=0),  # login
        MagicMock(returncode=0),  # tag
    ]

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = []
    mock_popen.return_value = mock_proc

    # Execute push using GHCR_TOKEN environment variable
    run_publish_flow(
        image="kuksa-databroker:vss-6.0",
        remote_tag="latest",
        token=None,
        username="bachvn1711",
        engine="docker",
        skip_login=False,
    )

    # Check login parameters (second call to run)
    login_call = mock_run.call_args_list[1]
    args, kwargs = login_call
    cmd = args[0]
    assert cmd == ["docker", "login", "ghcr.io", "-u", "bachvn1711", "--password-stdin"]
    assert kwargs["input"] == "env_token_123"


@patch("vssctl.commands.publish.resolve_engine")
@patch("subprocess.run")
@patch.dict(os.environ, {"CR_PAT": "cr_pat_token_456"}, clear=True)
def test_publish_login_failure(mock_run, mock_resolve):
    mock_resolve.return_value = "docker"
    # Inspect (success), Login (fails)
    mock_run.side_effect = [
        MagicMock(returncode=0),  # inspect
        subprocess.CalledProcessError(returncode=1, cmd="login", stderr="Access Denied"),  # login
    ]

    with pytest.raises(typer.Exit):
        run_publish_flow(
            image="kuksa-databroker:vss-6.0",
            remote_tag="latest",
            token=None,
            username="bachvn1711",
            engine="docker",
            skip_login=False,
        )


@patch("platform.machine", return_value="amd64")
@patch("vssctl.commands.build.resolve_engine")
@patch("vssctl.commands.build.find_build_context")
@patch("vssctl.commands.build.find_latest_vss_file")
@patch("shutil.copy2")
@patch("subprocess.Popen")
@patch("vssctl.commands.publish.run_publish_flow")
def test_build_with_publish_shortcut(
    mock_publish, mock_popen, mock_copy, mock_find_latest, mock_context, mock_resolve, mock_machine, tmp_path
):
    mock_resolve.return_value = "podman"

    build_dir = tmp_path / "databroker"
    build_dir.mkdir()
    (build_dir / "Cargo.toml").touch()
    mock_context.return_value = build_dir

    vss_file = tmp_path / "vss_release_6.0.json"
    vss_file.touch()
    mock_find_latest.return_value = vss_file

    # Build Popen mock
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = ["Successfully built image"]
    mock_popen.return_value = mock_process

    # Run build with --publish flag
    build_run(
        vss_file=vss_file,
        tag="custom:tag",
        engine="auto",
        databroker_dir=build_dir,
        no_cache=True,
        publish=True,
        token="my_token",
        username="bachvn1711",
        remote_tag="vss6.0",
        skip_login=True,
    )

    # Verify run_publish_flow was called with correct tag and params
    mock_publish.assert_called_once_with(
        image="custom:tag",
        remote_tag="vss6.0",
        token="my_token",
        username="bachvn1711",
        engine="podman",
        skip_login=True,
    )


@patch("vssctl.commands.publish.resolve_engine", return_value="docker")
@patch("subprocess.run")
@patch("subprocess.Popen")
@patch.dict(os.environ, {"GHCR_TOKEN": "environment-token", "CR_PAT": "fallback-token"}, clear=True)
def test_explicit_token_precedes_environment_and_default_tag(mock_popen, mock_run, mock_resolve):
    mock_run.return_value = MagicMock(returncode=0)
    mock_popen.return_value = MagicMock(returncode=0, stdout=[])

    remote_uri = run_publish_flow(
        image="kuksa-databroker:vss-6.0",
        remote_tag=None,
        token="explicit-token",
        username="example",
        engine="docker",
        skip_login=False,
    )

    assert remote_uri == "ghcr.io/example/databroker:vss-6.0"
    login_call = mock_run.call_args_list[1]
    assert login_call.kwargs["input"] == "explicit-token"


@patch("vssctl.commands.publish.resolve_engine", return_value="docker")
@patch("subprocess.run")
def test_publish_tag_failure_returns_one(mock_run, mock_resolve):
    mock_run.side_effect = [
        MagicMock(returncode=0),
        subprocess.CalledProcessError(1, ["docker", "tag"], stderr=b"tag failed"),
    ]

    with pytest.raises(typer.Exit) as exc_info:
        run_publish_flow(
            image="local:test",
            remote_tag="test",
            token=None,
            username="example",
            engine="docker",
            skip_login=True,
        )
    assert exc_info.value.exit_code == 1


@patch("vssctl.commands.publish.resolve_engine", return_value="docker")
@patch("subprocess.run")
@patch("subprocess.Popen")
def test_publish_push_failure_returns_one(mock_popen, mock_run, mock_resolve):
    mock_run.return_value = MagicMock(returncode=0)
    mock_popen.return_value = MagicMock(returncode=7, stdout=["push failed"])

    with pytest.raises(typer.Exit) as exc_info:
        run_publish_flow(
            image="local:test",
            remote_tag="test",
            token=None,
            username="example",
            engine="docker",
            skip_login=True,
        )
    assert exc_info.value.exit_code == 1
