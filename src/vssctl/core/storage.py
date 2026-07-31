import yaml
from pathlib import Path

from .models import Catalog
from vssctl.core.paths import SIGNALS_BASE_YAML, SIGNALS_CUSTOM_YAML


class Storage:

    def load_base(self) -> Catalog:
        if not SIGNALS_BASE_YAML.exists():
            return Catalog()
        with SIGNALS_BASE_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return Catalog()
        return Catalog.model_validate(data)

    def load_custom(self) -> Catalog:
        if not SIGNALS_CUSTOM_YAML.exists():
            return Catalog()
        with SIGNALS_CUSTOM_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return Catalog()
        return Catalog.model_validate(data)

    def load(self) -> Catalog:
        # Default load maps to custom catalog
        return self.load_custom()

    def save_base(self, catalog: Catalog):
        SIGNALS_BASE_YAML.parent.mkdir(parents=True, exist_ok=True)
        with SIGNALS_BASE_YAML.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                catalog.model_dump(),
                f,
                sort_keys=False,
            )

    def save_custom(self, catalog: Catalog):
        SIGNALS_CUSTOM_YAML.parent.mkdir(parents=True, exist_ok=True)
        with SIGNALS_CUSTOM_YAML.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                catalog.model_dump(),
                f,
                sort_keys=False,
            )

    def save(self, catalog: Catalog):
        # Default save maps to custom catalog
        self.save_custom(catalog)