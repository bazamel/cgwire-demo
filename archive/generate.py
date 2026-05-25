"""
fixtures/generate.py
--------------------
Main entry point.  Run with:

    python -m fixtures.generate

or simply:

    python fixtures/generate.py

Edit fixtures/config.py to control what gets created without touching this file.
"""

import gazu

# Local modules
import config
from people      import setup_admin, get_or_create_department, create_people
from assets      import ensure_asset_types, create_assets
from shots       import create_shot_hierarchy
from scheduling  import schedule_asset_tasks, schedule_shot_tasks
from previews    import get_statuses, apply_asset_previews, apply_shot_previews
from casting     import apply_casting


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_task_types(names: list[str]) -> dict[str, dict]:
    return {name: gazu.task.get_task_type_by_name(name) for name in names}


# ---------------------------------------------------------------------------
# Production builder
# ---------------------------------------------------------------------------

def build_production(prod_cfg: dict, asset_types: dict, people: dict):
    """
    Create a single production (project) with all its assets, shots, tasks,
    previews, and casting.
    """
    print(f"\n=== Building production: {prod_cfg['name']} ===")

    # 1. Create project
    project = gazu.project.new_project(
        prod_cfg["name"],
        production_type=prod_cfg.get("production_type", "short"),
    )

    # Upload thumbnail if provided
    if prod_cfg.get("thumbnail"):
        gazu.client.upload(
            f"/pictures/thumbnails/projects/{project['id']}",
            prod_cfg["thumbnail"],
        )

    # 2. Assets
    asset_cfg = prod_cfg.get("assets", [])
    assets    = create_assets(project, asset_cfg, asset_types)
    assets_by_name = {a["name"]: a for a in assets}
    print(f"  Created {len(assets)} assets")

    # 3. Shot hierarchy
    episodes_cfg = prod_cfg.get("episodes", [])
    _, sequences, shots = create_shot_hierarchy(
        project, episodes_cfg,
        frames_min=config.FRAMES_MIN,
        frames_max=config.FRAMES_MAX,
    )
    print(f"  Created {len(shots)} shots across {len(sequences)} sequences")

    # 4. Task types
    task_types = _get_task_types([
        "Modeling", "Rigging", "Storyboard", "Animation", "Rendering", "Compositing",
    ])

    # 5. Schedule asset tasks
    shot_start = schedule_asset_tasks(
        assets,
        modeling_type  = task_types["Modeling"],
        rigging_type   = task_types["Rigging"],
        project_start  = config.PROJECT_START,
        task_duration  = config.ASSET_TASK_DURATION,
    )
    print(f"  Scheduled asset tasks; shot tasks start {shot_start}")

    # 6. Schedule shot tasks
    seq_anim_cfg    = prod_cfg.get("sequence_animators", {})
    seq_anim_people = {
        int(seq_idx): people[name]
        for seq_idx, name in seq_anim_cfg.items()
        if name in people
    }
    schedule_shot_tasks(
        shots,
        sequences,
        task_types        = task_types,
        sequence_animators= seq_anim_people,
        start_cursor      = shot_start,
        task_duration     = config.SHOT_TASK_DURATION,
    )
    print(f"  Scheduled shot tasks")

    # 7. Casting
    casting_cfg  = prod_cfg.get("casting", [])
    casting_shots = prod_cfg.get("casting_shots", 0)
    if casting_cfg and casting_shots:
        apply_casting(project, shots, assets_by_name, casting_cfg, casting_shots)
        print(f"  Applied casting to first {casting_shots} shots")

    # 8. Statuses & previews
    statuses = get_statuses()
    apply_asset_previews(
        assets, asset_cfg, task_types, statuses,
        task_duration_days=config.ASSET_TASK_DURATION,
    )
    apply_shot_previews(
        shots, task_types, statuses,
        preview_roots=prod_cfg.get("preview_roots", {}),
    )
    print(f"  Applied previews and statuses")

    return project


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # --- Connect ---
    gazu.set_host(config.KITSU_HOST)
    gazu.log_in(config.ADMIN_EMAIL, config.ADMIN_PASSWORD)
    print(f"Connected to {config.KITSU_HOST}")

    # --- Admin ---
    setup_admin({**config.ADMIN_DISPLAY, "email": config.ADMIN_EMAIL})
    print("Admin account updated")

    # --- People ---
    department = get_or_create_department(config.DEFAULT_DEPARTMENT)
    people     = create_people(config.PEOPLE, department)
    print(f"Created {len(people)} people in department '{config.DEFAULT_DEPARTMENT}'")

    # --- Asset types ---
    asset_types = ensure_asset_types(config.ASSET_TYPES)
    print(f"Ensured {len(asset_types)} asset types")

    # --- Productions ---
    for prod_cfg in config.PRODUCTIONS:
        build_production(prod_cfg, asset_types, people)

    print("\nDone!")


if __name__ == "__main__":
    main()