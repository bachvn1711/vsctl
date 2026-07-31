from pathlib import Path

import yaml

from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal
from vssctl.core.storage import Storage


def clean_catalog():
    for name in ("signals.yaml", "signals-custom.yaml", "signals-base.yaml"):
        path = Path("workspace/catalog") / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump(
                {
                    "version": "0.1",
                    "signals": [],
                },
                f,
                sort_keys=False,
            )


def test_add_signal():

    clean_catalog()

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


def test_remove_signal():

    clean_catalog()

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


def test_search_signal():

    clean_catalog()

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


def test_list_signal():

    clean_catalog()

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


def test_storage_load_save():

    clean_catalog()

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