"""
fixtures/assets.py
------------------
Functions for creating asset types and assets.
"""

import gazu


def ensure_asset_types(type_names: list[str]) -> dict[str, dict]:
    """
    Return a mapping of asset-type name → object, creating any that are missing.
    """
    asset_types: dict[str, dict] = {}
    for name in type_names:
        at = gazu.asset.get_asset_type_by_name(name)
        if at is None:
            at = gazu.asset.new_asset_type(name)
        asset_types[name] = at
    return asset_types


def create_assets(
    project: dict,
    asset_cfg: list[tuple],          # (type_name, asset_name, preview_path?)
    asset_types: dict[str, dict],
) -> list[dict]:
    """
    Create all assets for *project*.

    Parameters
    ----------
    project      : project object
    asset_cfg    : list of 2- or 3-tuples:
                   (asset_type_name, asset_name)
                   (asset_type_name, asset_name, preview_path)
    asset_types  : mapping returned by ensure_asset_types()

    Returns
    -------
    list of created asset objects (same order as asset_cfg)
    """
    assets: list[dict] = []
    for entry in asset_cfg:
        type_name, asset_name = entry[0], entry[1]
        asset = gazu.asset.new_asset(project, asset_types[type_name], asset_name)
        assets.append(asset)
    return assets