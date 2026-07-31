import json
import re
from typing import Set

from vssctl.core import paths
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

_cached_baseline_paths = None


def get_baseline_paths() -> Set[str]:
    """
    Parses vss_release_6.0.json template to return a set of all standard VSS node paths.
    """
    global _cached_baseline_paths
    if _cached_baseline_paths is not None:
        return _cached_baseline_paths

    template_path = paths.VSS_CORE_TEMPLATES / "vss_release_6.0.json"
    if not template_path.exists():
        _cached_baseline_paths = set()
        return _cached_baseline_paths

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        paths_set = set()

        def recurse(node, prefix=""):
            if not isinstance(node, dict):
                return
            for key, val in node.items():
                if isinstance(val, dict):
                    # Skip standard VSS leaf node metadata attributes
                    if key in ("children", "description", "type", "datatype", "unit", "writable", "minimum", "maximum", "uuid"):
                        continue
                    current_path = f"{prefix}.{key}" if prefix else key
                    paths_set.add(current_path)
                    if "children" in val:
                        recurse(val["children"], current_path)

        recurse(data)
        _cached_baseline_paths = paths_set
        return _cached_baseline_paths
    except Exception:
        _cached_baseline_paths = set()
        return _cached_baseline_paths


class Validator:

    NAME_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*$")

    def validate(self, signal, catalog):
        self.validate_name(signal)
        self.validate_datatype(signal)
        self.validate_duplicate(signal, catalog)
        self.validate_parent(signal, catalog)
        self.validate_description(signal)
        self.validate_unit(signal)

    def validate_name(self, signal):
        if not self.NAME_PATTERN.match(signal.name):
            raise InvalidNameError(
                f"Invalid signal name: {signal.name}"
            )

    def validate_datatype(self, signal):
        if signal.datatype is None:
            return

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

    def validate_parent(self, signal, catalog=None):
        if not signal.parent.startswith("Vehicle"):
            raise InvalidParentError(signal.parent)

        baseline_paths = get_baseline_paths()

        # Compute custom branch paths explicitly declared in catalog (datatype is None)
        custom_branches = set()
        if catalog and catalog.signals:
            for item in catalog.signals:
                if item.datatype is None:
                    custom_branches.add(f"{item.parent}.{item.name}")

        # The parent path must exist in baseline_paths or custom_branches
        if signal.parent not in baseline_paths and signal.parent not in custom_branches:
            if signal.parent != "Vehicle":
                raise InvalidParentError(
                    f"Parent path '{signal.parent}' does not exist in VSS baseline or custom branches catalog."
                )

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