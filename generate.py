import os
import math
import random
import gazu
import requests
import tempfile
from datetime import date, datetime, timedelta

import random

from faker import Faker
fake = Faker()

gazu.set_host("http://localhost/api")
gazu.log_in("admin@example.com", "mysecretpassword")

AVATAR_API_URL = "https://i.pravatar.cc/300"  # random fake avatar per request
PASSWORD = "mysecretpassword"

persons = []
artists = []
projects = []
episodes = []
sequences = []
shots = []
assets = []
tasks = []

# Tracks minutes already logged per (artist_id, date_str) across all tasks.
# This ensures no artist ever exceeds 720 min (12 h) on a single calendar day,
# even when they are assigned to multiple shots whose pipelines overlap.
_artist_day_budget: dict[tuple[str, str], int] = {}

MAX_DAILY_MINUTES = 720  # 12 hours


def _download_avatar(seed):
    """Download a random fake avatar image and return the local file path."""
    response = requests.get(f"{AVATAR_API_URL}?u={seed}", timeout=10)
    response.raise_for_status()
 
    tmp_file = tempfile.NamedTemporaryFile(
        suffix=".png", prefix="avatar_", delete=False
    )
    tmp_file.write(response.content)
    tmp_file.close()
    return tmp_file.name
 
 
def _create_person(role, department=None):
    """Generate a fake person, create it in Kitsu, set its avatar, and
    optionally attach it to a department."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    email = f"{first_name.lower()}.{last_name.lower()}.{fake.unique.random_int(min=1000, max=99999)}@cg-wire.com"
    phone = "+33 6 82 38 19 08"
 
    try:
        person = gazu.person.new_person(
            first_name,
            last_name,
            email,
            phone,
            role,
            "",
            None,
            PASSWORD,
        )

        person['position'] = "artist"
        person['daily_salary'] = "500"

        if role == 'supervisor' or role == "manager":
            person['position'] = "lead"

        if role == 'vendor':
            person['contract_type'] = 'freelance'

        person = gazu.person.update_person(person)

    except gazu.exception.ParameterException as exc:
        # Surface the actual server message instead of the opaque
        # ('data/persons', True) repr, and skip this person rather than
        # aborting the whole generation run.
        message = exc.args[1] if len(exc.args) > 1 else str(exc)
        print(f"Skipping {full_name} <{email}>: server rejected payload: {message}")
        return None
 
    avatar_path = None
    # gazu.person.set_avatar(person, "fixtures/fake_user/alicia.png")
    try:
        avatar_path = _download_avatar(person["id"])
        gazu.person.set_avatar(person, avatar_path)
    except requests.RequestException as exc:
        print(f"Could not fetch avatar for {full_name}: {exc}")
    finally:
        if avatar_path and os.path.exists(avatar_path):
            os.remove(avatar_path)
 
    if department is not None:
        try:
            gazu.person.add_person_to_department(person, department)
        except Exception as exc:
            print(
                f"Could not add {full_name} to department "
                f"{department.get('name', department)}: {exc}"
            )
 
    persons.append(person)
    if role in ("user", "vendor"):
        artists.append(person)
 
    return person

def generatePeople(n_per_department=10):
    """Generate fake people for the studio.
 
    - Kitsu stays the single admin user.
    - Two generic clients are created.
    - For each existing department, `n_per_department` people are created:
        * 1 supervisor
        * 1 manager (producer)
        * 20% of the remaining headcount as vendors
        * the rest as artists ("user" role), assigned to that department
    """
    # --- Admin: keep Kitsu as the one and only admin user ---
    admin = gazu.person.get_person_by_email("admin@example.com")
 
    gazu.person.set_avatar(admin, "fixtures/fake_user/kitsu.png")
 
    admin["first_name"] = "Kitsu"
    admin["last_name"] = ""
    admin["full_name"] = "Kitsu"
 
    gazu.person.update_person(
        {
            "id": admin["id"],
            "full_name": admin["full_name"],
            "first_name": admin["first_name"],
            "last_name": admin["last_name"],
        }
    )
    persons.append(admin)
 
    # --- Clients: two generic clients, not tied to a department ---
    for _ in range(2):
        _create_person("client")
 
    # --- Departments: supervisor + manager + vendors + artists per department ---
    departments = gazu.person.all_departments()
 
    if not departments:
        print("No departments found, skipping department staffing.")
        return persons, artists
 
    for department in departments:
        # 1 supervisor, 1 manager (producer) per department
        _create_person("supervisor", department)
        _create_person("manager", department)
 
        remaining = max(n_per_department - 2, 0)
        n_vendors = math.floor(remaining * 0.2)
        n_artists = remaining - n_vendors
 
        for _ in range(n_vendors):
            _create_person("vendor", department)
 
        for _ in range(n_artists):
            _create_person("user", department)
 
    return persons, artists

def generateProductions(size):
    for i in range(size):
        projects.append(gazu.project.new_project(fake.name(), production_type="tvshow"))

def generateAssets():
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

    for (asset_type, asset_name) in asset_desc:
        for i in range(len(projects)):
            project = projects[i]
            assets.append(
                gazu.asset.new_asset(project, asset_type, asset_name)
            )

def generateEpisodes(size):
    for i in range(len(projects)):
        project = projects[i]

        for i in range(size):
            episodes.append(gazu.shot.new_episode(project, f"E{i:05d}"))

def generateSequences(size):
    for i in range(len(episodes)):
        episode = episodes[i]

        for i in range(size):
            sequences.append(gazu.shot.new_sequence(
            episode["project_id"], f"SQ{i:05d}", episode=episode))

def generateShots(size):
    for i in range(len(sequences)):
        sequence = sequences[i]

        for i in range(size):
            shots.append(gazu.shot.new_shot(
            sequence["project_id"], sequence, f"SH{i:05d}",
                    nb_frames=random.randrange(20, 90, 1)))

TASK_SCHEDULE = {
    "Storyboard":   {"start_offset": 0,  "duration": 7},
    "Layout":       {"start_offset": 7,  "duration": 7},
    "Animation":    {"start_offset": 14, "duration": 14},
    "Rendering":    {"start_offset": 28, "duration": 7},
    "Compositing":  {"start_offset": 35, "duration": 7},
}

# How many days to shift each successive shot forward so their pipelines don't overlap.
# The full pipeline is 42 days (0 → 35+7), so an interval of 7 days means SH00001
# starts 7 days after SH00000, SH00002 starts 14 days after SH00000, etc.
SHOT_INTERVAL_DAYS = 7

now = datetime.now()
month = now.month - 3
year = now.year if month > 0 else now.year - 1
month = month if month > 0 else month + 12

PROJECT_START = datetime(year, month, now.day)

done = gazu.task.get_task_status_by_name("Done")
retake = gazu.task.get_task_status_by_name("Retake")
wfa  = gazu.task.get_task_status_by_name("Waiting For Approval")
wip  = gazu.task.get_task_status_by_name("Work In Progress")
todo = gazu.task.get_task_status_by_name("Todo")

def _task_datetime(start: datetime, due: datetime, fraction: float, jitter_minutes: int = 120) -> str:
    """
    Returns an ISO-8601 datetime string at `fraction` of the way through
    the task window, plus a small random offset.
    
    fraction: 0.0 = start_date, 1.0 = due_date
    jitter_minutes: max random offset applied after the fractional point
    """
    span = (due - start).total_seconds()
    base = start + timedelta(seconds=span * fraction)
    jitter = timedelta(minutes=random.randint(0, jitter_minutes))
    return (base + jitter).strftime("%Y-%m-%dT%H:%M:%S")


def _shot_index(shot_name: str) -> int:
    """
    Extract the zero-based numeric index from a shot name like 'SH00000', 'SH00001', etc.
    Falls back to 0 for any unexpected format.
    """
    try:
        # Strip leading 'SH' then parse the integer (handles leading zeros)
        return int(shot_name[2:])
    except (ValueError, IndexError):
        return 0

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

TASK_DEPARTMENT_MAP = {
    "Storyboard": "Storyboard",
    "Layout": "Layout",
    "Animation": "Animation",
    "Rendering": "Rendering",
    "Compositing": "Compositing",
}

def get_artist_for_task(task_type):
    department_name = TASK_DEPARTMENT_MAP.get(task_type["name"])

    candidates = []
    for artist in artists:
        person = gazu.person.get_person(artist["id"], relations=True)

        if "departments" not in person:
            continue

        for dept_id in person["departments"]:
            dept = gazu.person.get_department(dept_id)
            if dept["name"] == department_name:
                candidates.append(artist)
                break

    return random.choice(candidates) if candidates else random.choice(artists)

def generateTask(shot, task_type, task_status):
    task   = gazu.task.new_task(shot, task_type)
    artist = get_artist_for_task(task_type)

    shot_offset = timedelta(days=_shot_index(shot["name"]) * SHOT_INTERVAL_DAYS)

    schedule = TASK_SCHEDULE.get(task_type["name"])
    if schedule:
        start = PROJECT_START + shot_offset + timedelta(days=schedule["start_offset"])
        due   = start + timedelta(days=schedule["duration"])
        task["start_date"] = start.strftime("%Y-%m-%d")
        task["real_start_date"] = task["start_date"]
        task["due_date"]   = due.strftime("%Y-%m-%d")
        task["created_at"]   = start.strftime("%Y-%m-%d")
        task["updated_at"]   = due.strftime("%Y-%m-%d")
        task["last_comment_date"]   = due.strftime("%Y-%m-%d")
        task["estimation"] = schedule["duration"] * 480 

        gazu.task.update_task(task)
    else:
        start = PROJECT_START + shot_offset
        due   = start + timedelta(days=30)
    
    gazu.client.put(
        f"/actions/persons/{artist['id']}/assign",
        {"task_ids": [task["id"]]}  # note: list, not bare string
    )

    # ── Timesheet generation ──────────────────────────────────────────────────
    _generate_timesheets(task, artist, start, due)
    # ─────────────────────────────────────────────────────────────────────────

    timestamp = _task_datetime(start, due, 0.0, jitter_minutes=60)

    # All tasks start at TODO
    comment = gazu.task.add_comment(
        task, todo, "Task created",
        created_at=timestamp,
        # updated_at=timestamp,
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment)

    if task_status == todo:
        return

    timestamp = _task_datetime(start, due, 0.25, jitter_minutes=120)
    # TODO → WIP
    comment = gazu.task.add_comment(
        task, wip, "Started work",
        created_at=timestamp,
        # updated_at=timestamp,
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment)

    if task_status == wip:
        return

    # ── Resolve preview file path ─────────────────────────────────────────────
    task_name = task_type["name"]
    shot_index = _shot_index(shot["name"])
    preview_path = None

    # if task_name == "Modeling":
    #     preview_path = file_paths_modeling[shot_index % len(file_paths_modeling)]
    if task_name == "Storyboard":
        preview_path = file_paths_sb[shot_index % len(file_paths_sb)]
    elif task_name == "Animation":
        movie_paths = movie_file_paths_animation
        still_paths = file_paths_animation
        if shot_index < len(movie_paths):
            preview_path = movie_paths[shot_index]
        else:
            preview_path = still_paths[shot_index % len(still_paths)]
    elif task_name == "Rendering":
        movie_paths = movie_file_paths_render
        still_paths = file_paths_render
        if shot_index < len(movie_paths):
            preview_path = movie_paths[shot_index]
        else:
            preview_path = still_paths[shot_index % len(still_paths)]
    # ─────────────────────────────────────────────────────────────────────────

    timestamp = _task_datetime(start, due, 0.75, jitter_minutes=120)
    # WIP → WFA
    wfa_comment = gazu.task.add_comment(
        task, wfa, "Ready for approval",
        created_at=timestamp,
        # updated_at=timestamp,
    )
    wfa_comment["updated_at"] = timestamp
    gazu.task.update_comment(wfa_comment)

    if preview_path:
        preview_file = gazu.task.add_preview(task, wfa_comment, preview_path)
        gazu.task.set_main_preview(preview_file)

    if task_status == wfa:
        return

    timestamp = _task_datetime(start, due, 0.85, jitter_minutes=60)
    # WFA → Retake  ← frontier is retake, stop here
    if task_status == retake:
        comment = gazu.task.add_comment(
            task, retake, "Changes requested",
            created_at=timestamp,
            # updated_at=timestamp,
        )
        comment["updated_at"] = timestamp
        gazu.task.update_comment(comment)
        return

    timestamp = _task_datetime(start, due, 1.0, jitter_minutes=0)
    # WFA → Done
    comment = gazu.task.add_comment(
        task, done, "Approved",
        created_at=timestamp,
        # updated_at=timestamp,
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment)
    task = gazu.task.get_task(task['id'])
    task['done_date'] = timestamp
    gazu.task.update_task(task)


def _generate_timesheets(task, artist, start: datetime, due: datetime) -> None:
    """
    Log daily timesheets for *artist* on *task* between start and due.

    Rules:
    - Skip weekends (Saturday / Sunday).
    - Normal days: 6–8 hours (360–480 min), drawn from a truncated-normal dist
      so most days cluster around 7 h.
    - 10 % of working days are "crunch": 8.5–12 hours (510–720 min).
    - 10 % of tasks are "late": the actual work window is extended by 1–5
      extra working days past the nominal due date.
    - An artist can never log more than 12 h (720 min) across all tasks on any
      single calendar day. When the budget is exhausted the remaining tasks for
      that day are silently skipped; partial logging is used when only part of
      the desired duration fits within the remaining budget.
    """
    is_late = random.random() < 0.10

    # Expand the working window for late tasks
    actual_end = due
    if is_late:
        extra_days = 0
        added = 0
        target_extra = random.randint(1, 5)          # 1-5 extra working days
        cursor = due + timedelta(days=1)
        while added < target_extra:
            if cursor.weekday() < 5:                 # Mon-Fri only
                added += 1
                actual_end = cursor
            cursor += timedelta(days=1)

    # Collect all working days in [start, actual_end]
    working_days: list[date] = []
    cursor = start
    while cursor <= actual_end:
        if cursor.weekday() < 5:                     # Mon–Fri
            working_days.append(cursor)
        cursor += timedelta(days=1)

    if not working_days:
        return

    artist_id = artist["id"]

    for work_date in working_days:
        date_str = work_date.strftime("%Y-%m-%d") if isinstance(work_date, datetime) else work_date.strftime("%Y-%m-%d")
        budget_key = (artist_id, date_str)

        # How many minutes has this artist already logged today (across all tasks)?
        already_logged = _artist_day_budget.get(budget_key, 0)
        remaining_budget = MAX_DAILY_MINUTES - already_logged

        if remaining_budget <= 0:
            # Artist is fully booked for this day — skip entirely.
            continue

        is_crunch = random.random() < 0.10

        if is_crunch:
            # Crunch: 8 h 30 min – 12 h
            desired = random.randint(510, 720)
        else:
            # Normal: 6–8 h with a soft bell around 7 h
            raw = random.gauss(mu=420, sigma=40)     # mean 7 h, σ 40 min
            desired = int(max(360, min(480, raw)))   # clamp to [6 h, 8 h]

        # Clamp to whatever budget is left for this artist today.
        duration = min(desired, remaining_budget)

        gazu.task.set_time_spent(
            task,
            artist,
            date_str,
            duration,
        )

        # Update the shared daily budget.
        _artist_day_budget[budget_key] = already_logged + duration

        
# Replace the random status logic with a cascading pipeline status.
# Each shot gets one "frontier" stage (the currently-active one); stages before
# it are Done, the frontier stage itself gets a random in-progress status
# (wip / wfa / retake), and stages after it are Todo.

PIPELINE_ORDER = ["Storyboard", "Layout", "Animation", "Rendering", "Compositing"]

def _shot_status_cascade(shot):
    """
    Returns a dict mapping task-type name → status for one shot.
    Picks a random frontier stage; everything before is Done, the frontier
    is randomly wip/wfa (10% retake), everything after is Todo.
    """
    frontier_idx = random.randint(0, len(PIPELINE_ORDER) - 1)
    frontier_status = random.choices(
        [wip, wfa, retake],
        weights=[50, 40, 10]
    )[0]

    statuses = {}
    for i, name in enumerate(PIPELINE_ORDER):
        if i < frontier_idx:
            statuses[name] = done
        elif i == frontier_idx:
            statuses[name] = frontier_status
        else:
            statuses[name] = todo
    return statuses


def generateTasks():
    storyboard  = gazu.task.get_task_type_by_name("Storyboard")
    layout      = gazu.task.get_task_type_by_name("Layout")
    animation   = gazu.task.get_task_type_by_name("Animation")
    render      = gazu.task.get_task_type_by_name("Rendering")
    compositing = gazu.task.get_task_type_by_name("Compositing")

    task_types = [storyboard, layout, animation, render, compositing]

    for shot in shots:
        cascade = _shot_status_cascade(shot)
        for task_type in task_types:
            status = cascade[task_type["name"]]
            generateTask(shot, task_type, status)

def generateBudget():
    for i in range(len(projects)):
        project = projects[i]
        budget = gazu.project.create_budget(project, "Production Budget", "Labor, hardware, and license costs.", "USD", PROJECT_START, PROJECT_START + timedelta(days=180), 2000000)

        for i in range(len(persons)):
            person = gazu.person.get_person(persons[i]["id"], relations = True)
            
            if 'departments' in person and len(person['departments']) > 0:
                gazu.client.post(f"data/projects/{project['id']}/budgets/{budget['id']}/entries", {
                    "budget_id": budget['id'],
                    "department_id": person['departments'][0],
                    "person_id": person['id'],
                    "start_date": PROJECT_START,
                    "months_duration": "6",
                    "daily_salary": person["daily_salary"],
                    "position": person["position"],
                    "seniority": "mid",
                })

generatePeople()
generateProductions(1)
generateAssets()
generateEpisodes(1)
generateSequences(1)
generateShots(50)
generateTasks()
generateBudget()