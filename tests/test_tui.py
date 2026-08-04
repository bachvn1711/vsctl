from vssctl.core.models import Catalog, Signal
from vssctl.core.tree_builder import TreeBuilder
from vssctl.tui.formatting import format_node_details
from vssctl.tui.state import matching_nodes


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
