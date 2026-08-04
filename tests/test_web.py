from pathlib import Path

from vssctl.web.app import create_app


def _write_catalog(directory: Path) -> None:
    (directory / "adas.yaml").write_text(
        "owner: ADAS Team\nversion: '1.1'\nsignals:\n  - parent: Vehicle.ADAS\n    name: Speed\n    datatype: float\n    unit: km/h\n    description: Vehicle speed\n",
        encoding="utf-8",
    )
    (directory / "body.yaml").write_text(
        "owner: Body Team\nsignals:\n  - parent: Vehicle.Body\n    name: DoorOpen\n    datatype: boolean\n    writable: true\n",
        encoding="utf-8",
    )


def test_web_health_and_dashboard(tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    client = create_app(tmp_path).test_client()
    assert client.get("/health").get_json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_web_api_aggregates_team_catalogs(tmp_path: Path) -> None:
    _write_catalog(tmp_path)
    client = create_app(tmp_path).test_client()
    stats = client.get("/api/v1/stats").get_json()
    assert stats["total_signals"] == 2
    assert stats["team_count"] == 2
    teams = client.get("/api/v1/teams").get_json()
    assert [team["name"] for team in teams] == ["ADAS Team", "Body Team"]
    tree = client.get("/api/v1/tree").get_json()
    assert tree["name"] == "Vehicle"
    signals = client.get("/api/v1/signals?owner=ADAS%20Team").get_json()
    assert [signal["path"] for signal in signals] == ["Vehicle.ADAS.Speed"]
    markdown = client.get("/docs/markdown")
    assert markdown.status_code == 200
    assert b"Vehicle.ADAS.Speed" in markdown.data
