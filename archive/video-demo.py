import os
import random
import gazu
from datetime import date, timedelta

gazu.set_host("http://localhost/api")
gazu.log_in("admin@example.com", "mysecretpassword")

admin = gazu.person.get_person_by_email("admin@example.com")

gazu.person.set_avatar(admin, "fixtures/fake_user/kitsu.png")

admin["first_name"] = "Kitsu"
admin["last_name"] = ""
admin["full_name"] = "Kitsu"

gazu.person.update_person({"id": admin["id"], "full_name": admin["full_name"], "first_name": admin["first_name"], "last_name": admin["last_name"]})

persons = [
    {
        "first_name": "Alicia",
        "last_name": "Cooper",
        "email": "alicia@cg-wire.com",
        "phone": "+33 6 82 38 19 08",
        "role": "user",
        "name": "alicia"
    },
    {
        "first_name": "Michael",
        "last_name": "Byrd",
        "email": "michael@cg-wire.com",
        "phone": "+33 6 32 45 12 45",
        "role": "user",
        "name": "michael"
    },
    {
        "first_name": "Ann",
        "last_name": "Kennedy",
        "email": "ann@cg-wire.com",
        "phone": "+33 6 32 45 12 45",
        "role": "user",
        "name": "ann"
    },
    {
        "first_name": "Brennan",
        "last_name": "Mason",
        "email": "brennan@cg-wire.com",
        "phone": "+33 6 43 42 13 21",
        "role": "user",
        "name": "brennan"
    },
    {
        "first_name": "David",
        "last_name": "Penna",
        "email": "david@cg-wire.com",
        "phone": "+33 6 08 98 92 12",
        "role": "user",
        "name": "david"
    },
    {
        "first_name": "Rachel",
        "last_name": "Shelton",
        "email": "rachel@cg-wire.com",
        "phone": "+33 6 92 38 91 23",
        "role": "user",
        "name": "rachel"
    },
    {
        "first_name": "Frank",
        "last_name": "Rousseau",
        "email": "frank@cg-wire.com",
        "phone": "+33 6 22 18 13 88",
        "role": "admin",
        "name": "frank"
    }
]

person_objects = []
for person in persons:
    personfull = gazu.person.new_person(
        person["first_name"],
        person["last_name"],
        person["email"],
        person["phone"],
        person["role"]
    )
    gazu.person.set_avatar(personfull, "fixtures/fake_user/%s.png" % person["name"])
    person_objects.append(personfull)

# Add all users to the Animation department
animation_department = gazu.person.get_department_by_name("Animation")
if animation_department is None:
    animation_department = gazu.person.new_department("Animation")

for person in person_objects:
    gazu.person.add_person_to_department(person, animation_department)

alicia = gazu.person.get_person_by_full_name("Alicia Cooper")
brennan = gazu.person.get_person_by_full_name("Brennan Mason")
david = gazu.person.get_person_by_full_name("David Penna")

bbb = gazu.project.new_project("Big Buck Bunny")
agent327 = gazu.project.new_project("Agent 327")
caminandes = gazu.project.new_project("Caminandes", production_type="tvshow")
characters = gazu.asset.new_asset_type("Characters")
props = gazu.asset.new_asset_type("Props")
environment = gazu.asset.new_asset_type("Environment")
fx = gazu.asset.new_asset_type("FX")

asset_desc = [
    (characters, "Lama"),
    (characters, "Oti"),
    (characters, "Pingoo"),
    (environment, "Mine"),
    (environment, "Pool"),
    (environment, "Railroad"),
    (environment, "Oil Machine"),
    (fx, "Smoke"),
    (fx, "Wind"),
    (props, "Berry"),
    (props, "Flower"),
    (props, "Mine Cart"),
    (props, "Train")
]

assets = []
shots = []

for (asset_type, asset_name) in asset_desc:
    assets.append(
        gazu.asset.new_asset(caminandes, asset_type, asset_name)
    )

sequences = []

for episode_name in ["E01"]:
    episode = gazu.shot.new_episode(caminandes, episode_name)

    for sequence_name in ["SE01", "SE02", "SE03"]:
        sequence = gazu.shot.new_sequence(
            caminandes, sequence_name, episode=episode)
        sequences.append(sequence)

        for shot_name in [
            "SH001", "SH002", "SH003", "SH004", "SH005", "SH006",
            "SH007", "SH008", "SH009", "SH010", "SH011"
        ]:
            shots.append(
                gazu.shot.new_shot(
                    caminandes,
                    sequence,
                    shot_name,
                    nb_frames=random.randrange(20, 90, 1)
                )
            )

for episode_name in ["E02"]:
    episode = gazu.shot.new_episode(caminandes, episode_name)

    for sequence_name in ["SE01", "SE02"]:
        sequence = gazu.shot.new_sequence(caminandes, sequence_name, episode=episode)
        sequences.append(sequence)

        for shot_name in ["SH001", "SH002", "SH003"]:
            shots.append(
                gazu.shot.new_shot(
                    caminandes,
                    sequence,
                    shot_name,
                    nb_frames=random.randrange(20, 90, 1)
                )
            )

for episode_name in ["E03"]:
    episode = gazu.shot.new_episode(caminandes, episode_name)

    for sequence_name in ["SE01", "SE02", "SE03"]:
        sequence = gazu.shot.new_sequence(
            caminandes, sequence_name, episode=episode)
        sequences.append(sequence)

        for shot_name in [
            "SH001", "SH002", "SH003", "SH004", "SH005", "SH006", "SH007"
        ]:
            shots.append(
                gazu.shot.new_shot(
                    caminandes,
                    sequence,
                    shot_name,
                    nb_frames=random.randrange(20, 90, 1)
                )
            )

modeling = gazu.task.get_task_type_by_name("Modeling")
setup = gazu.task.get_task_type_by_name("Rigging")
storyboard = gazu.task.get_task_type_by_name("Storyboard")
layout = gazu.task.get_task_type_by_name("Layout")
animation = gazu.task.get_task_type_by_name("Animation")
render = gazu.task.get_task_type_by_name("Rendering")
compositing = gazu.task.get_task_type_by_name("Compositing")

# --- Date helpers ---
PROJECT_START = date(2024, 1, 8)  # Monday
ASSET_TASK_DURATION = 5           # working days per asset task
SHOT_TASK_DURATION = 3            # working days per shot task

def add_working_days(start: date, days: int) -> date:
    """Advance `start` by `days` Mon–Fri working days."""
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon–Fri
            added += 1
    return current

def date_str(d: date) -> str:
    return d.isoformat()

# --- Asset tasks (modeling then rigging, sequential per asset) ---
asset_cursor = PROJECT_START

for asset in assets:
    # Modeling
    m_start = asset_cursor
    m_due   = add_working_days(m_start, ASSET_TASK_DURATION)
    task_modeling = gazu.task.new_task(
        asset, modeling,
        # start_date=date_str(m_start),
        # due_date=date_str(m_due)
    )

    # Rigging starts after modeling finishes
    s_start = add_working_days(m_due, 1)
    s_due   = add_working_days(s_start, ASSET_TASK_DURATION)
    task_setup = gazu.task.new_task(
        asset, setup,
        # start_date=date_str(s_start),
        # due_date=date_str(s_due)
    )

    # Advance cursor so next asset starts after this one's rigging
    asset_cursor = add_working_days(s_due, 1)

# Shot tasks start after all assets are done
shot_cursor = asset_cursor

for shot in shots:
    sb_start = shot_cursor
    sb_due   = add_working_days(sb_start, SHOT_TASK_DURATION)
    gazu.task.new_task(
        shot, storyboard,
        # start_date=date_str(sb_start),
        # due_date=date_str(sb_due)
    )

    anim_start = add_working_days(sb_due, 1)
    anim_due   = add_working_days(anim_start, SHOT_TASK_DURATION)
    animation_task = gazu.task.new_task(
        shot, animation,
        # start_date=date_str(anim_start),
        # due_date=date_str(anim_due)
    )

    render_start = add_working_days(anim_due, 1)
    render_due   = add_working_days(render_start, SHOT_TASK_DURATION)
    gazu.task.new_task(
        shot, render,
        # start_date=date_str(render_start),
        # due_date=date_str(render_due)
    )

    comp_start = add_working_days(render_due, 1)
    comp_due   = add_working_days(comp_start, SHOT_TASK_DURATION)
    gazu.task.new_task(
        shot, compositing,
        # start_date=date_str(comp_start),
        # due_date=date_str(comp_due)
    )

    # Assign animation tasks per sequence
    if shot["parent_id"] == sequences[0]["id"]:
        gazu.task.assign_task(animation_task, alicia)
    if shot["parent_id"] == sequences[1]["id"]:
        gazu.task.assign_task(animation_task, brennan)
    if shot["parent_id"] == sequences[2]["id"]:
        gazu.task.assign_task(animation_task, david)

    # Advance cursor: next shot starts after compositing
    shot_cursor = add_working_days(comp_due, 1)


lama   = gazu.asset.get_asset_by_name(caminandes, "Lama")
pingoo = gazu.asset.get_asset_by_name(caminandes, "Pingoo")
berry  = gazu.asset.get_asset_by_name(caminandes, "Berry")

casting = [
    {"asset_id": lama["id"],   "nb_occurences": 1},
    {"asset_id": pingoo["id"], "nb_occurences": 1},
    {"asset_id": berry["id"],  "nb_occurences": 2}
]

gazu.casting.update_shot_casting(caminandes, shots[0], casting)
gazu.casting.update_shot_casting(caminandes, shots[1], casting)
gazu.casting.update_shot_casting(caminandes, shots[2], casting)
gazu.casting.update_shot_casting(caminandes, shots[3], casting)

gazu.client.upload(
    "/pictures/thumbnails/projects/%s" % caminandes["id"],
    "fixtures/v1.png"
)

file_paths_modeling = [
    "fixtures/th_assets/lama.png",
    "fixtures/th_assets/ep01/oti.png",
    "fixtures/th_assets/ep01/pingoo.png",
    "fixtures/th_assets/ep01/mine.png",
    "fixtures/th_assets/ep01/pool.png",
    "fixtures/th_assets/ep01/railroad.jpg",
    "fixtures/th_assets/ep01/oil_machine.png",
    "fixtures/th_assets/ep01/smoke.png",
    "fixtures/th_assets/ep01/wind.png",
    "fixtures/th_assets/ep01/berry.png",
    "fixtures/th_assets/ep01/flower.png",
    "fixtures/th_assets/ep01/cart.png",
    "fixtures/th_assets/ep01/train.png",
]

file_paths_sb = [
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH01.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH02.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH03.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH04.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH05.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH06.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH07.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH08.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH09.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH10.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE01_SH11.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH01.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH02.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH03.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH04.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH05.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH06.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH07.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH08.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH09.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH10.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE02_SH11.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH01.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH02.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH03.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH04.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH05.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH06.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH07.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH08.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH09.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH10.png",
    "fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE03_SH11.png",
]

file_paths_animation = [
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH01.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH02.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH03.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH04.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH05.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH06.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH07.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH08.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH09.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH10.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH11.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH01.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH02.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH03.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH04.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH05.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH06.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH07.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH08.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH09.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH10.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE02_SH11.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH01.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH02.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH03.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH04.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH05.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH06.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH07.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH08.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH09.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH10.png",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE03_SH11.png",
]

file_paths_render = [
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH01.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH02.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH03.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH04.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH05.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH06.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH07.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH08.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH09.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH10.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH11.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH01.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH02.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH03.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH04.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH05.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH06.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH07.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH08.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH09.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH10.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE02_SH11.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH01.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH02.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH03.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH04.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH05.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH06.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH07.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH08.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH09.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH10.png",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE03_SH11.png",
]

movie_file_paths_animation = [
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH01.mp4",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH02.mp4",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH03.mp4",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH04.mp4",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH05.mp4",
    "fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH06.mp4",
]

movie_file_paths_render = [
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH01.mp4",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH02.mp4",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH03.mp4",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH04.mp4",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH05.mp4",
    "fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH06.mp4",
]

done = gazu.task.get_task_status_by_name("Done")
wfa  = gazu.task.get_task_status_by_name("Waiting For Approval")
wip  = gazu.task.get_task_status_by_name("Work In Progress")

# Asset previews & statuses
for (index, asset) in enumerate(assets):
    task_modeling = gazu.task.get_task_by_entity(asset, modeling)
    if index < len(file_paths_modeling) and \
       os.path.exists(file_paths_modeling[index]):
        comment = gazu.task.add_comment(
            task_modeling, wfa, "New preview",
            # duration=ASSET_TASK_DURATION * 8 * 3600
        )
        preview_file = gazu.task.add_preview(
            task_modeling, comment, file_paths_modeling[index]
        )
        gazu.task.set_main_preview(preview_file)
        comment = gazu.task.add_comment(
            task_modeling, done, "Done",
            # duration=0
        )
    else:
        # No preview file — leave some as WFA to populate that status
        gazu.task.add_comment(
            task_modeling, wfa, "Ready for review",
            duration=ASSET_TASK_DURATION * 8 * 3600
        )

    task_setup = gazu.task.get_task_by_entity(asset, setup)
    gazu.task.add_comment(task_setup, wip, "Getting started")

# Shot previews & statuses
for (index, shot) in enumerate(shots):
    time_spent = SHOT_TASK_DURATION * 8 * 3600  # 3 days in seconds

    # Storyboard
    if index < len(file_paths_sb) and os.path.exists(file_paths_sb[index]):
        task_sb = gazu.task.get_task_by_entity(shot, storyboard)
        comment = gazu.task.add_comment(
            task_sb, wfa, "New preview"
        )
        preview_file = gazu.task.add_preview(task_sb, comment, file_paths_sb[index])
        gazu.task.set_main_preview(preview_file)
        comment = gazu.task.add_comment(task_sb, done, "Done")

    # Animation
    task_animation = gazu.task.get_task_by_entity(shot, animation)
    if index < len(file_paths_animation) and \
       os.path.exists(file_paths_animation[index]):
        comment = gazu.task.add_comment(
            task_animation, wfa, "New preview"
        )
        preview_file = gazu.task.add_preview(
            task_animation, comment, file_paths_animation[index]
        )
        gazu.task.set_main_preview(preview_file)
        # Every 3rd shot stays as WFA instead of being marked Done
        if index % 3 != 2:
            gazu.task.add_comment(task_animation, done, "Done")
    elif index < len(movie_file_paths_animation) and \
         os.path.exists(movie_file_paths_animation[index]):
        comment = gazu.task.add_comment(
            task_animation, wfa, "New preview"
        )
        gazu.task.add_preview(task_animation, comment, movie_file_paths_animation[index])
        if index % 3 != 2:
            gazu.task.add_comment(task_animation, done, "Done")
    else:
        # No file — set as WFA with time logged
        gazu.task.add_comment(
            task_animation, wfa, "Ready for review"
        )

    # Render
    task_render = gazu.task.get_task_by_entity(shot, render)
    if index < len(file_paths_render) and \
       os.path.exists(file_paths_render[index]):
        comment = gazu.task.add_comment(
            task_render, wfa, "New preview"
        )
        preview_file = gazu.task.add_preview(
            task_render, comment, file_paths_render[index]
        )
        gazu.task.set_main_preview(preview_file)
        if index % 4 != 3:
            gazu.task.add_comment(task_render, done, "Done")
    elif index < len(movie_file_paths_render) and \
         os.path.exists(movie_file_paths_render[index]):
        comment = gazu.task.add_comment(
            task_render, wfa, "New preview"
        )
        gazu.task.add_preview(task_render, comment, movie_file_paths_render[index])
        if index % 4 != 3:
            gazu.task.add_comment(task_render, done, "Done")
    else:
        gazu.task.add_comment(
            task_render, wfa, "Ready for review"
        )
