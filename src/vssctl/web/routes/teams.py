from __future__ import annotations

from flask import Blueprint, render_template

from .common import aggregate

teams = Blueprint("teams", __name__)


@teams.get("/teams")
def index():
    return render_template("teams.html", teams=aggregate().teams())
