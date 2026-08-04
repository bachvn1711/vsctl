import pytest

from vssctl.core.models import Catalog, Signal
from vssctl.core.storage import Storage
from vssctl.core.tree_builder import TreeBuilder
from vssctl.tui.formatting import format_node_details
from vssctl.tui.state import BrowserLoadError, BrowserState, CatalogSource, matching_nodes


def _tree():
    catalog = Catalog(signals=[
        Signal(parent="Vehicle", name="Speed", datatype="float", unit="km/h", description="Vehicle speed"),
        Signal(parent="Vehicle.Cabin", name="Temperature", datatype="float", description="Cabin temperature"),
    ])
    return TreeBuilder().build(catalog)


def test_matching_nodes_matches_path_and_description():
    root = _tree()
    matches = matching_nodes(root, "temperature")
    assert [node.path for node in matches] == ["Vehicle.Cabin.Temperature"]


def test_format_node_details_contains_signal_metadata():
    node = _tree().find("Vehicle.Speed")
    assert node is not None
    details = format_node_details(node)
    assert "Datatype: float" in details
    assert "Unit: km/h" in details


def test_empty_query_returns_entire_tree():
    root = _tree()
    assert [node.path for node in matching_nodes(root, "")] == [
        "Vehicle", "Vehicle.Speed", "Vehicle.Cabin", "Vehicle.Cabin.Temperature"
    ]


def test_browser_state_loads_selected_sources_and_custom_overrides_base(isolated_workspace):
    storage = Storage()
    storage.save_base(Catalog(signals=[
        Signal(parent="Vehicle", name="Speed", datatype="float", description="Base speed"),
    ]))
    storage.save_custom(Catalog(signals=[
        Signal(parent="Vehicle", name="Speed", datatype="float", description="Custom speed"),
        Signal(parent="Vehicle.Cabin", name="Temperature", datatype="float", description="Temperature"),
    ]))

    base = BrowserState.load(CatalogSource.BASE)
    custom = BrowserState.load(CatalogSource.CUSTOM)
    merged = BrowserState.load(CatalogSource.MERGED)

    assert [signal.name for signal in base.catalog.signals] == ["Speed"]
    assert {signal.name for signal in custom.catalog.signals} == {"Speed", "Temperature"}
    merged_speed = next(signal for signal in merged.catalog.signals if signal.name == "Speed")
    assert merged_speed.description == "Custom speed"


@pytest.mark.parametrize("source", list(CatalogSource))
def test_browser_state_rejects_empty_catalog(source, isolated_workspace):
    with pytest.raises(BrowserLoadError, match=f"{source.value} catalog is empty"):
        BrowserState.load(source)
