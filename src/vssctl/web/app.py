from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from vssctl.core.paths import CATALOG_DIR
from vssctl.web.catalog import CatalogAggregator, CatalogLoadError
from vssctl.web.routes.api import api
from vssctl.web.routes.dashboard import dashboard
from vssctl.web.routes.explorer import explorer
from vssctl.web.routes.reports import reports
from vssctl.web.routes.teams import teams


def create_app(catalog_path: str | Path | None = None) -> Flask:
    """Create the read-only vssctl dashboard application."""
    catalog_dir = Path(catalog_path) if catalog_path is not None else CATALOG_DIR
    app = Flask(__name__)
    app.config["VSSCTL_CATALOG_DIR"] = catalog_dir.resolve()
    app.extensions["vssctl_catalog"] = CatalogAggregator(app.config["VSSCTL_CATALOG_DIR"])
    for blueprint in (dashboard, explorer, teams, reports, api):
        app.register_blueprint(blueprint)

    @app.get("/health")
    def health() -> tuple[Any, int]:
        return jsonify({"status": "ok"}), 200

    @app.errorhandler(CatalogLoadError)
    def catalog_error(error: CatalogLoadError) -> tuple[Any, int]:
        if request.path.startswith("/api/"):
            return jsonify({"error": str(error)}), 400
        return render_template("error.html", message=str(error)), 400

    return app
