from __future__ import annotations

from pathlib import Path

from flask import Blueprint, Response, abort, render_template, send_file

from vssctl.core.paths import COMPANY_VSPEC, JSON_TREE_DIR

from .common import aggregate

reports = Blueprint("reports", __name__)


@reports.get("/reports")
def index():
    catalog = aggregate()
    return render_template("reports.html", stats=catalog.stats(), duplicates=catalog.duplicates)


@reports.get("/docs")
def docs():
    return render_template("docs.html", signals=aggregate().signals)


@reports.get("/docs/markdown")
def markdown_docs() -> Response:
    lines = ["# vssctl Catalog", "", "| Path | Owner | Since | Datatype | Description |", "|---|---|---|---|---|"]
    for signal in aggregate().signals:
        description = signal.description.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {signal.path} | {signal.owner} | {signal.since or '-'} | {signal.datatype or 'branch'} | {description} |")
    return Response("\n".join(lines) + "\n", mimetype="text/markdown", headers={"Content-Disposition": "attachment; filename=vssctl-catalog.md"})


@reports.get("/downloads/<artifact>")
def download(artifact: str):
    known: dict[str, Path] = {"company.vspec": COMPANY_VSPEC, "vss_release_6.0.json": JSON_TREE_DIR / "vss_release_6.0.json"}
    path = known.get(artifact)
    if path is None or not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True, download_name=path.name)
