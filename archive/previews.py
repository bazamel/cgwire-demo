"""
fixtures/previews.py
--------------------
Functions for adding comments, previews, and task statuses to assets and shots.
"""

import os
import gazu


# ---------------------------------------------------------------------------
# Statuses (fetched once at module level after login)
# ---------------------------------------------------------------------------

def get_statuses() -> dict[str, dict]:
    """Return a dict of the three core task-status objects."""
    return {
        "done": gazu.task.get_task_status_by_name("Done"),
        "wfa":  gazu.task.get_task_status_by_name("Waiting For Approval"),
        "wip":  gazu.task.get_task_status_by_name("Work In Progress"),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_preview(task: dict, status: dict, preview_path: str, comment_text: str):
    """Add a comment + preview file to *task*, setting it as the main preview."""
    comment      = gazu.task.add_comment(task, status, comment_text)
    preview_file = gazu.task.add_preview(task, comment, preview_path)
    gazu.task.set_main_preview(preview_file)
    return preview_file


def _try_preview(task: dict, status_wfa: dict, paths: list[str], comment: str) -> bool:
    """Try each path in *paths*; add the first one that exists. Return success."""
    for path in paths:
        if path and os.path.exists(path):
            _add_preview(task, status_wfa, path, comment)
            return True
    return False


# ---------------------------------------------------------------------------
# Asset previews
# ---------------------------------------------------------------------------

def apply_asset_previews(
    assets: list[dict],
    asset_cfg: list[tuple],     # (type_name, asset_name, preview_path?)
    task_types: dict[str, dict],
    statuses: dict[str, dict],
    task_duration_days: int,
):
    """
    For each asset:
    - Modeling: add preview + mark Done (or leave as WFA if no file)
    - Rigging:  mark WIP
    """
    done = statuses["done"]
    wfa  = statuses["wfa"]
    wip  = statuses["wip"]
    modeling = task_types["Modeling"]
    setup    = task_types["Rigging"]

    for index, asset in enumerate(assets):
        preview_path = asset_cfg[index][2] if len(asset_cfg[index]) > 2 else None

        task_modeling = gazu.task.get_task_by_entity(asset, modeling)
        if _try_preview(task_modeling, wfa, [preview_path], "New preview"):
            gazu.task.add_comment(task_modeling, done, "Done")
        else:
            gazu.task.add_comment(
                task_modeling, wfa, "Ready for review",
                duration=task_duration_days * 8 * 3600,
            )

        task_setup = gazu.task.get_task_by_entity(asset, setup)
        gazu.task.add_comment(task_setup, wip, "Getting started")


# ---------------------------------------------------------------------------
# Shot previews
# ---------------------------------------------------------------------------

def _shot_preview_paths(
    shot_index: int,
    task_name: str,
    preview_roots: dict[str, str],
    shots: list[dict],
) -> tuple[list[str], list[str]]:
    """
    Derive (image_candidates, movie_candidates) for a given shot index.

    This follows the original naming convention:
        <root>/caminandes_llamigos_<episode>_<sequence>_<shot>.{png,jpg,mp4}

    Falls back to an empty list when the root is absent from config.
    """
    root = preview_roots.get(task_name, "")
    if not root:
        return [], []

    # We don't have direct episode/sequence metadata on the shot object here,
    # so we reconstruct the flat shot index → filename mapping that the
    # original script used via parallel lists.
    #
    # The naming pattern in the original fixtures was a fixed prefix + E01 +
    # SE0x + SHyyy, listed in creation order.  Rather than re-derive episode
    # structure, we just use the shot's index position within the flat list,
    # which mirrors the original approach of parallel arrays.

    # Build a numbered name like "shot_0001"
    base = f"shot_{shot_index:04d}"

    # For projects that supply real fixture paths, callers can pass a resolved
    # list instead (see resolve_preview_path).  This fallback returns empty so
    # the caller degrades gracefully.
    return [], []


def resolve_preview_paths(
    shots: list[dict],
    preview_roots: dict[str, str],
) -> dict[str, list[str]]:
    """
    Build task-name → [path_for_shot_0, path_for_shot_1, …] from a glob of
    the preview root directories.

    For each task root the function expects files named with the shot's flat
    index order matching how the shots list is ordered (same convention as the
    original script's parallel arrays).  Missing files are stored as empty
    strings so index alignment is preserved.

    Supports .png, .jpg, and .mp4 extensions.
    """
    import glob

    resolved: dict[str, list[str]] = {}

    for task_name, root in preview_roots.items():
        if not os.path.isdir(root):
            resolved[task_name] = [""] * len(shots)
            continue

        # Collect all image and movie files sorted by name
        candidates = sorted(
            glob.glob(os.path.join(root, "*.png"))
            + glob.glob(os.path.join(root, "*.jpg"))
        )
        movies = sorted(glob.glob(os.path.join(root, "*.mp4")))

        img_paths   = candidates + [""] * len(shots)
        movie_paths = movies     + [""] * len(shots)

        resolved[task_name] = [
            (img_paths[i], movie_paths[i]) for i in range(len(shots))
        ]

    return resolved


def apply_shot_previews(
    shots: list[dict],
    task_types: dict[str, dict],
    statuses: dict[str, dict],
    preview_roots: dict[str, str],
):
    """
    For each shot apply storyboard, animation, rendering statuses and previews.
    """
    done = statuses["done"]
    wfa  = statuses["wfa"]

    storyboard_type = task_types["Storyboard"]
    animation_type  = task_types["Animation"]
    rendering_type  = task_types["Rendering"]

    path_map = resolve_preview_paths(shots, preview_roots)

    def get_paths(task_name: str, i: int) -> tuple[str, str]:
        entries = path_map.get(task_name, [])
        if i < len(entries):
            entry = entries[i]
            if isinstance(entry, tuple):
                return entry          # (img_path, movie_path)
            return entry, ""          # legacy plain string
        return "", ""

    for index, shot in enumerate(shots):
        # ---- Storyboard ----------------------------------------------------
        img, _ = get_paths("Storyboard", index)
        task_sb = gazu.task.get_task_by_entity(shot, storyboard_type)
        if _try_preview(task_sb, wfa, [img], "New preview"):
            gazu.task.add_comment(task_sb, done, "Done")

        # ---- Animation -----------------------------------------------------
        img, mov = get_paths("Animation", index)
        task_anim = gazu.task.get_task_by_entity(shot, animation_type)
        had_file = _try_preview(task_anim, wfa, [img, mov], "New preview")
        if not had_file:
            gazu.task.add_comment(task_anim, wfa, "Ready for review")
        elif index % 3 != 2:
            gazu.task.add_comment(task_anim, done, "Done")

        # ---- Rendering -----------------------------------------------------
        img, mov = get_paths("Rendering", index)
        task_render = gazu.task.get_task_by_entity(shot, rendering_type)
        had_file = _try_preview(task_render, wfa, [img, mov], "New preview")
        if not had_file:
            gazu.task.add_comment(task_render, wfa, "Ready for review")
        elif index % 4 != 3:
            gazu.task.add_comment(task_render, done, "Done")