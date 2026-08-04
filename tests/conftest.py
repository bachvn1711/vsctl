from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil

import pytest

from vssctl.config import settings
from vssctl.core import baseline, paths, storage, validator


CANONICAL_VSS_CORE_TEMPLATES = paths.VSS_CORE_TEMPLATES


@dataclass(frozen=True)
class IsolatedWorkspace:
    root: Path
    catalog_dir: Path
    generated_dir: Path
    templates_dir: Path
    signals_base: Path
    signals_custom: Path


@pytest.fixture(autouse=True)
def reset_global_settings():
    original = {
        "databroker_path": settings.databroker_path,
        "output_dir": settings.output_dir,
        "engine": settings.engine,
        "ghcr_org": settings.ghcr_org,
        "vss_version": settings.vss_version,
        "verbose": settings.verbose,
        "quiet": settings.quiet,
    }
    validator._cached_baseline_paths = None
    try:
        yield
    finally:
        validator._cached_baseline_paths = None
        for name, value in original.items():
            setattr(settings, name, value)


@pytest.fixture
def isolated_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> IsolatedWorkspace:
    root = tmp_path / "repo"
    workspace = root / "workspace"
    catalog_dir = workspace / "catalog"
    generated_dir = workspace / "generated"
    templates_dir = workspace / "templates"
    signals_base = catalog_dir / "signals-base.yaml"
    signals_custom = catalog_dir / "signals-custom.yaml"

    catalog_dir.mkdir(parents=True)
    generated_dir.mkdir(parents=True)
    (templates_dir / "spec").mkdir(parents=True)
    (templates_dir / "vss-core").mkdir(parents=True)
    canonical_baseline = CANONICAL_VSS_CORE_TEMPLATES / "vss_release_6.0.json"
    if canonical_baseline.is_file():
        shutil.copy2(canonical_baseline, templates_dir / "vss-core" / canonical_baseline.name)

    replacements = {
        "PROJECT_ROOT": root,
        "WORKSPACE": workspace,
        "CATALOG_DIR": catalog_dir,
        "GENERATED_DIR": generated_dir,
        "BUILD_DIR": workspace / "build",
        "MERGED_DIR": generated_dir / "merged",
        "TEAM_VSS_BASE": templates_dir / "spec",
        "VSS_CORE_TEMPLATES": templates_dir / "vss-core",
        "JSON_TREE_DIR": generated_dir / "json_tree",
        "SIGNALS_BASE_YAML": signals_base,
        "SIGNALS_CUSTOM_YAML": signals_custom,
        "SIGNALS_YAML": signals_custom,
        "TREE_JSON": generated_dir / "tree.json",
        "COMPANY_VSPEC": generated_dir / "company.vspec",
        "METADATA_JSON": generated_dir / "vss_release_6.0.json",
    }
    for name, value in replacements.items():
        monkeypatch.setattr(paths, name, value)

    monkeypatch.setattr(storage, "SIGNALS_BASE_YAML", signals_base)
    monkeypatch.setattr(storage, "SIGNALS_CUSTOM_YAML", signals_custom)
    monkeypatch.setattr(baseline, "VSS_CORE_TEMPLATES", replacements["VSS_CORE_TEMPLATES"])
    monkeypatch.setattr(baseline, "JSON_TREE_DIR", replacements["JSON_TREE_DIR"])

    return IsolatedWorkspace(
        root=root,
        catalog_dir=catalog_dir,
        generated_dir=generated_dir,
        templates_dir=templates_dir,
        signals_base=signals_base,
        signals_custom=signals_custom,
    )
