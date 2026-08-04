from __future__ import annotations

from flask import Blueprint, jsonify, request

from vssctl.core.catalog import CatalogService
from vssctl.core.models import Signal
from vssctl.core.validator import Validator

from .common import aggregate

api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.get("/tree")
def tree():
    return jsonify(aggregate().tree())


@api.get("/signals")
def signals():
    catalog = aggregate()
    result = catalog.filtered(request.args.get("owner"), request.args.get("datatype"), request.args.get("since"))
    return jsonify([signal.as_dict() for signal in result])


@api.post("/signals")
def add_signal():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    try:
        for field in ("datatype", "unit", "description"):
            if payload.get(field) == "":
                payload[field] = None if field != "description" else ""
        signal = Signal.model_validate(payload)
        CatalogService().add(signal)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"path": f"{signal.parent}.{signal.name}", "message": "Signal added."}), 201


@api.post("/validate")
def validate_catalog():
    catalog = CatalogService().catalog
    validator = Validator()
    issues: list[dict[str, str]] = []
    for signal in catalog.signals:
        try:
            validator.validate(signal, catalog)
        except Exception as exc:
            issues.append({"path": f"{signal.parent}.{signal.name}", "error": str(exc)})
    return jsonify({"valid": not issues, "issues": issues, "checked": len(catalog.signals)})


@api.post("/actions/generate")
def generate_action():
    try:
        from vssctl.commands.generate import run
        run(version=None)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True, "message": "Generation completed."})


@api.post("/actions/build")
def build_action():
    try:
        from vssctl.commands.build import run
        run(vss_file=None, tag=None, engine="auto", databroker_dir=None, no_cache=False, publish=False, token=None, username="bachvn1711", remote_tag=None, skip_login=False)
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify({"ok": True, "message": "Container build completed."})


@api.get("/teams")
def teams():
    return jsonify(aggregate().teams())


@api.get("/stats")
def stats():
    return jsonify(aggregate().stats())
