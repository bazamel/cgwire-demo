"""
fixtures/casting.py
-------------------
Functions for applying asset casting to shots.
"""

import gazu


def apply_casting(
    project: dict,
    shots: list[dict],
    assets_by_name: dict[str, dict],   # asset_name → asset object
    casting_cfg: list[dict],            # [{"asset_name": …, "nb_occurences": …}]
    num_shots: int,
):
    """
    Apply *casting_cfg* to the first *num_shots* shots in *shots*.

    Parameters
    ----------
    project        : project object
    shots          : flat list of shot objects (in creation order)
    assets_by_name : mapping built from the assets list
    casting_cfg    : list of {"asset_name": str, "nb_occurences": int}
    num_shots      : how many shots (from the front of *shots*) to cast
    """
    casting = []
    for entry in casting_cfg:
        asset = assets_by_name.get(entry["asset_name"])
        if asset is None:
            print(f"[casting] WARNING: asset '{entry['asset_name']}' not found – skipped")
            continue
        casting.append({"asset_id": asset["id"], "nb_occurences": entry["nb_occurences"]})

    for shot in shots[:num_shots]:
        gazu.casting.update_shot_casting(project, shot, casting)