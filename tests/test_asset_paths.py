from pathlib import Path

import pytest
from jobsies.asset_paths import get_asset_path
from jobsies.settings import get_settings


def test_asset_paths_resolve_in_source_checkout() -> None:
    """Resolve docs and configs from the repository when package copies are absent."""
    assert (get_asset_path("docs") / "plugins.md").is_file()
    assert (get_asset_path("configs") / "default_jobsies_configs.json").is_file()


def test_asset_paths_prefer_package_assets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Prefer assets installed inside the Python package over source-tree copies."""
    package_root = tmp_path / "site-packages" / "jobsies"
    packaged_docs = package_root / "docs"
    packaged_docs.mkdir(parents=True)
    source_root = tmp_path / "source"
    (source_root / "docs").mkdir(parents=True)

    monkeypatch.setattr("jobsies.asset_paths._PACKAGE_ROOT", package_root)
    monkeypatch.setattr("jobsies.asset_paths._SOURCE_ROOT", source_root)

    assert get_asset_path("docs") == packaged_docs


def test_web_assets_resolve_from_the_installed_package() -> None:
    """Resolve templates and static assets relative to the Jobsies package."""
    settings = get_settings()

    assert (Path(settings.templates_location_) / "documentation.html").is_file()
    assert (Path(settings.static_location_) / "css" / "style.css").is_file()
