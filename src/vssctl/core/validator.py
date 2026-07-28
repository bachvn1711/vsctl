from .constants import SUPPORTED_TYPES
from .exceptions import *
import re
from .constants import SUPPORTED_UNITS
PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")

class Validator:

    def validate(self, signal, catalog):
        self.validate_name(signal)
        self.validate_datatype(signal)
        self.validate_duplicate(signal, catalog)
        self.validate_parent(signal)
        self.validate_description(signal)
        self.validate_unit(signal)


def validate_name(self, signal):

    if not PATTERN.match(signal.name):
        raise InvalidNameError(
            f"Invalid signal name: {signal.name}"
        )

def validate_datatype(self, signal):

    if signal.datatype not in SUPPORTED_TYPES:

        raise InvalidDatatypeError(
            signal.datatype
        )

def validate_description(self, signal):

    if not signal.description.strip():

        raise ValidationError(
            "Description cannot be empty."
        )

def validate_duplicate(self, signal, catalog):

    for item in catalog.signals:

        if (
            item.parent == signal.parent
            and item.name == signal.name
        ):
            raise DuplicateSignalError(
                f"{signal.parent}.{signal.name}"
            )

def validate_parent(self, signal):

    if not signal.parent.startswith("Vehicle"):

        raise InvalidParentError(
            signal.parent
        )

def validate_unit(self, signal):

    if signal.unit is None:
        return

    if signal.unit not in SUPPORTED_UNITS:
        raise InvalidUnitError(signal.unit)