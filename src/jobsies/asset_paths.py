from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent
_SOURCE_ROOT = _PACKAGE_ROOT.parent.parent


def get_asset_path(asset_name: str) -> Path:
    """Locate an asset directory in the installed package or source checkout."""
    packaged_path = _PACKAGE_ROOT / asset_name
    if packaged_path.is_dir():
        return packaged_path
    return _SOURCE_ROOT / asset_name
