import re

from vssctl.core.constants import (
    SUPPORTED_TYPES,
    SUPPORTED_UNITS,
)

from vssctl.core.exceptions import (
    ValidationError,
    DuplicateSignalError,
    InvalidDatatypeError,
    InvalidParentError,
    InvalidNameError,
    InvalidUnitError,
)


class Validator:

    NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")

    def validate(self, signal, catalog):

        self.validate_name(signal)
        self.validate_datatype(signal)
        self.validate_duplicate(signal, catalog)
        self.validate_parent(signal)
        self.validate_description(signal)
        self.validate_unit(signal)

    def validate_name(self, signal):

        if not self.NAME_PATTERN.match(signal.name):
            raise InvalidNameError(
                f"Invalid signal name: {signal.name}"
            )

    def validate_datatype(self, signal):

        if signal.datatype not in SUPPORTED_TYPES:
            raise InvalidDatatypeError(signal.datatype)

    def validate_duplicate(self, signal, catalog):

        for item in catalog.signals:

            if (
                item.parent == signal.parent
                and item.name == signal.name
            ):
                raise DuplicateSignalError(
                    f"Signal '{signal.parent}.{signal.name}' already exists."
                )

    def validate_parent(self, signal):

        if not signal.parent.startswith("Vehicle"):
            raise InvalidParentError(signal.parent)

    def validate_description(self, signal):

        if not signal.description.strip():
            raise ValidationError(
                "Description cannot be empty."
            )

    def validate_unit(self, signal):

        if signal.unit is None or signal.unit == "":
            return

        if signal.unit not in SUPPORTED_UNITS:
            raise InvalidUnitError(signal.unit)