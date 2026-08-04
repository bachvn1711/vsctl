from vssctl.core.baseline import custom_signals
from vssctl.core.baseline import baseline_signal_paths, output_signal_paths
from vssctl.core.models import Signal


def test_custom_signals_are_classified_by_full_path():
    signals = [
        Signal(parent="Vehicle", name="Speed", datatype="float"),
        Signal(parent="Vehicle.Custom", name="Mode", datatype="string"),
    ]
    assert [signal.name for signal in custom_signals(signals, {"Vehicle.Speed"})] == ["Mode"]


def test_output_baseline_is_available_for_classification():
    paths = baseline_signal_paths("6.0")
    assert "Vehicle" in paths


def test_output_json_extra_paths_are_custom():
    assert "Vehicle.ADAS.RPM" in output_signal_paths("6.0") - baseline_signal_paths("6.0")
