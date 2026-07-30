import pytest

from vssctl.core.models import Catalog
from vssctl.core.models import Signal

from vssctl.core.validator import Validator

from vssctl.core.exceptions import (
    DuplicateSignalError,
    InvalidDatatypeError,
    InvalidNameError,
    InvalidParentError,
    InvalidUnitError,
    ValidationError,
)


validator = Validator()


def test_valid_signal():

    catalog = Catalog()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
    )

    validator.validate(
        signal,
        catalog,
    )


def test_duplicate_signal():

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
    )

    catalog = Catalog(
        signals=[signal]
    )

    with pytest.raises(DuplicateSignalError):
        validator.validate(
            signal,
            catalog,
        )


def test_invalid_datatype():

    catalog = Catalog()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="abc",
        description="Vehicle speed",
    )

    with pytest.raises(
        InvalidDatatypeError
    ):
        validator.validate(
            signal,
            catalog,
        )


def test_invalid_name():

    catalog = Catalog()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="speed",
        datatype="float",
        description="Vehicle speed",
    )

    with pytest.raises(
        InvalidNameError
    ):
        validator.validate(
            signal,
            catalog,
        )


def test_invalid_parent():

    catalog = Catalog()

    signal = Signal(
        parent="ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
    )

    with pytest.raises(
        InvalidParentError
    ):
        validator.validate(
            signal,
            catalog,
        )


def test_invalid_unit():

    catalog = Catalog()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="Vehicle speed",
        unit="abc",
    )

    with pytest.raises(
        InvalidUnitError
    ):
        validator.validate(
            signal,
            catalog,
        )


def test_empty_description():

    catalog = Catalog()

    signal = Signal(
        parent="Vehicle.ADAS",
        name="Speed",
        datatype="float",
        description="",
    )

    with pytest.raises(
        ValidationError
    ):
        validator.validate(
            signal,
            catalog,
        )


def test_valid_branch():
    catalog = Catalog()
    signal = Signal(
        parent="Vehicle.ADAS",
        name="CustomBranch",
        datatype=None,
        description="A custom branch description",
    )
    validator.validate(signal, catalog)