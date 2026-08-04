from __future__ import annotations

from flask import Blueprint, abort, render_template, send_file

from vssctl.config import settings
from vssctl.core.paths import PROJECT_ROOT

from .common import aggregate

dashboard = Blueprint("dashboard", __name__)


@dashboard.get("/")
def index():
    catalog = aggregate()
    return render_template("dashboard.html", stats=catalog.stats(), teams=catalog.teams(), image=f"ghcr.io/{settings.ghcr_org}/vssctl")


@dashboard.get("/brand/logo")
def logo():
    path = PROJECT_ROOT / "src" / "vssctl" / "logo" / "vssctl_logo.png"
    if not path.is_file():
        abort(404)
    return send_file(path, mimetype="image/png", max_age=3600)
