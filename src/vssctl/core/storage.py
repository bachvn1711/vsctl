from pathlib import Path

import yaml

from .models import Catalog

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CATALOG = PROJECT_ROOT / "workspace" / "catalog" / "signals.yaml"


class Storage:

    def load(self) -> Catalog:

        if not CATALOG.exists():
            return Catalog()

        with open(CATALOG) as f:
            data = yaml.safe_load(f)

        return Catalog.model_validate(data)

    def save(self, catalog: Catalog):

        CATALOG.parent.mkdir(parents=True, exist_ok=True)

        with open(CATALOG, "w") as f:

            yaml.safe_dump(

                catalog.model_dump(),

                f,

                sort_keys=False,

            )