from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal
from vssctl.core.storage import Storage


def test_add_signal(isolated_workspace):

    service = CatalogService()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
    )

    service.add(signal)

    catalog = Storage().load()

    assert len(catalog.signals) == 1

    assert catalog.signals[0].name == "Speed"


def test_remove_signal(isolated_workspace):

    service = CatalogService()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
    )

    service.add(signal)

    service.remove(
        "Vehicle.ADAS",
        "Speed",
    )

    catalog = Storage().load()

    assert len(catalog.signals) == 0


def test_search_signal(isolated_workspace):

    service = CatalogService()

    service.add(
        Signal(
            parent="Vehicle.ADAS",
            name="Speed",
            datatype="float",
            description="Vehicle speed",
        )
    )

    service.add(
        Signal(
            parent="Vehicle.Body",
            name="DoorOpen",
            datatype="boolean",
            description="Door status",
        )
    )

    result = service.search("speed")

    assert len(result) == 1

    assert result[0].name == "Speed"


def test_list_signal(isolated_workspace):

    service = CatalogService()

    service.add(
        Signal(
            parent="Vehicle.ADAS",
            name="Speed",
            datatype="float",
            description="Vehicle speed",
        )
    )

    signals = service.list()

    assert len(signals) == 1


def test_storage_load_save(isolated_workspace):

    storage = Storage()

    catalog = storage.load()

    catalog.signals.append(
        Signal(
            parent="Vehicle.ADAS",
            name="RPM",
            datatype="int32",
            description="Engine RPM",
        )
    )

    storage.save(catalog)

    loaded = storage.load()

    assert len(loaded.signals) == 1

    assert loaded.signals[0].name == "RPM"
