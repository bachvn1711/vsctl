from pathlib import Path

import yaml

from .models import Catalog

from pathlib import Path

from vssctl.core.paths import SIGNALS_YAML
# CATALOG = PROJECT_ROOT / "workspace" / "catalog" / "signals.yaml"


class Storage:

    def load(self) -> Catalog:

        if not SIGNALS_YAML.exists():
            return Catalog()

        with SIGNALS_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return Catalog.model_validate(data)

    def save(self, catalog: Catalog):

        SIGNALS_YAML.parent.mkdir(parents=True, exist_ok=True)

        with SIGNALS_YAML.open("w", encoding="utf-8") as f:

            yaml.safe_dump(

                catalog.model_dump(),

                f,

                sort_keys=False,

            )