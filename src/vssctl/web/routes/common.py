from __future__ import annotations

from typing import cast

from flask import current_app

from vssctl.web.catalog import CatalogAggregate, CatalogAggregator


def aggregate() -> CatalogAggregate:
    aggregator = cast(CatalogAggregator, current_app.extensions["vssctl_catalog"])
    return aggregator.load()
