from __future__ import annotations

from flask import Blueprint, render_template

explorer = Blueprint("explorer", __name__)


@explorer.get("/explorer")
def index():
    return render_template("explorer.html")
