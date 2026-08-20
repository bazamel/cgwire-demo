import os
import math
import random
import threading
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

import gazu
import requests
from faker import Faker

fake = Faker()

# ── Configuration ─────────────────────────────────────────────────────────────
HOST = "http://localhost/api"
LOGIN = "admin@example.com"
PASSWORD = "mysecretpassword"

WORKERS = 12            # threads used for task/timesheet generation
WITH_AVATARS = True     # set False to skip all avatar downloads
WITH_PREVIEWS = True    # set False to skip preview uploads (big speed win)
AVATAR_POOL_SIZE = 15   # avatars downloaded once and reused across persons

AVATAR_API_URL = "https://i.pravatar.cc/300"
MAX_DAILY_MINUTES = 720  # 12 hours
# ──────────────────────────────────────────────────────────────────────────────

gazu.set_host(HOST)
gazu.log_in(LOGIN, PASSWORD)

persons = []
artists = []
projects = []
episodes = []
sequences = []
shots = []
assets = []
tasks = []

# Built once during generatePeople(); replaces the per-task API lookups that
# used to dominate runtime.
_artists_by_department: dict[str, list[dict]] = {}
_person_department_id: dict[str, str] = {}

# Tracks minutes already logged per (artist_id, date_str) across all tasks.
# Guarded by a lock because timesheets are generated from multiple threads.
_artist_day_budget: dict[tuple[str, str], int] = {}
_budget_lock = threading.Lock()

_avatar_pool: list[str] = []


# ── Thread-local Kitsu clients ────────────────────────────────────────────────
# gazu's default client wraps a requests.Session, which is NOT safe to share
# across threads. Each worker thread gets its own authenticated client.
_local = threading.local()


def client():
    """Return this thread's authenticated KitsuClient."""
    c = getattr(_local, "client", None)
    if c is None:
        c = gazu.client.create_client(HOST)
        gazu.log_in(LOGIN, PASSWORD, client=c)
        _local.client = c
    return c
# ──────────────────────────────────────────────────────────────────────────────


def _build_avatar_pool():
    """Download a small pool of avatars once and reuse them for every person.

    The original script hit pravatar.cc once per person over the public
    internet, serially — by far the slowest part of person creation.
    """
    if not WITH_AVATARS:
        return

    for i in range(AVATAR_POOL_SIZE):
        try:
            response = requests.get(f"{AVATAR_API_URL}?u={i}", timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Could not fetch avatar #{i}: {exc}")
            continue

        tmp_file = tempfile.NamedTemporaryFile(
            suffix=".png", prefix="avatar_", delete=False
        )
        tmp_file.write(response.content)
        tmp_file.close()
        _avatar_pool.append(tmp_file.name)


def _cleanup_avatar_pool():
    for path in _avatar_pool:
        if os.path.exists(path):
            os.remove(path)
    _avatar_pool.clear()


def _create_person(role, department=None):
    """Generate a fake person, create it in Kitsu, set its avatar, and
    optionally attach it to a department."""
    first_name = fake.first_name()
    last_name = fake.last_name()
    full_name = f"{first_name} {last_name}"
    email = (
        f"{first_name.lower()}.{last_name.lower()}."
        f"{fake.unique.random_int(min=1000, max=99999)}@cg-wire.com"
    )
    phone = "+33 6 82 38 19 08"

    try:
        person = gazu.person.new_person(
            first_name,
            last_name,
            email,
            phone,
            role,
            "",
            [department] if department is not None else None,
            PASSWORD,
            contract_type="freelance" if role == "vendor" else "open-ended",
        )

        person["position"] = "lead" if role in ("supervisor", "manager") else "artist"
        person["daily_salary"] = "500"

        person = gazu.person.update_person(person)

    except gazu.exception.ParameterException as exc:
        # Surface the actual server message instead of the opaque
        # ('data/persons', True) repr, and skip this person rather than
        # aborting the whole generation run.
        message = exc.args[1] if len(exc.args) > 1 else str(exc)
        print(f"Skipping {full_name} <{email}>: server rejected payload: {message}")
        return None

    if _avatar_pool:
        try:
            gazu.person.set_avatar(person, random.choice(_avatar_pool))
        except Exception as exc:
            print(f"Could not set avatar for {full_name}: {exc}")

    # Remember the department locally so we never have to ask the server again.
    if department is not None:
        _person_department_id[person["id"]] = department["id"]
        if role in ("user", "vendor"):
            _artists_by_department.setdefault(department["name"], []).append(person)

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
    _build_avatar_pool()

    # --- Admin: keep Kitsu as the one and only admin user ---
    admin = gazu.person.get_person_by_email(LOGIN)

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
        projects.append(
            gazu.project.new_project(fake.name(), production_type="tvshow")
        )


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
        (props, "Train"),
    ]

    for (asset_type, asset_name) in asset_desc:
        for i in range(len(projects)):
            project = projects[i]
            assets.append(gazu.asset.new_asset(project, asset_type, asset_name))


def generateEpisodes(size):
    for i in range(len(projects)):
        project = projects[i]

        for i in range(size):
            episodes.append(gazu.shot.new_episode(project, f"E{i:05d}"))


def generateSequences(size):
    for i in range(len(episodes)):
        episode = episodes[i]

        for i in range(size):
            sequences.append(
                gazu.shot.new_sequence(
                    episode["project_id"], f"SQ{i:05d}", episode=episode
                )
            )


def generateShots(size):
    for i in range(len(sequences)):
        sequence = sequences[i]

        for i in range(size):
            shots.append(
                gazu.shot.new_shot(
                    sequence["project_id"],
                    sequence,
                    f"SH{i:05d}",
                    nb_frames=random.randrange(20, 90, 1),
                )
            )


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

# Clamp the day so e.g. "3 months before the 31st" never lands on a short month.
_last_day = (datetime(year + (month == 12), (month % 12) + 1, 1) - timedelta(days=1)).day
PROJECT_START = datetime(year, month, min(now.day, _last_day))

done = gazu.task.get_task_status_by_name("Done")
retake = gazu.task.get_task_status_by_name("Retake")
wfa = gazu.task.get_task_status_by_name("Waiting For Approval")
wip = gazu.task.get_task_status_by_name("Work In Progress")
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
    f"fixtures/th_shots/ep01/SB/caminandes_llamigos_E01_SE{se:02d}_SH{sh:02d}.png"
    for se in range(1, 4)
    for sh in range(1, 12)
]

file_paths_animation = [
    f"fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE{se:02d}_SH{sh:02d}.png"
    for se in range(1, 4)
    for sh in range(1, 12)
]

file_paths_render = [
    f"fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE{se:02d}_SH{sh:02d}.png"
    for se in range(1, 4)
    for sh in range(1, 12)
]

movie_file_paths_animation = [
    f"fixtures/th_shots/ep01/Anim/caminandes_llamigos_E01_SE01_SH{sh:02d}.mp4"
    for sh in range(1, 7)
]

movie_file_paths_render = [
    f"fixtures/th_shots/ep01/render/caminandes_llamigos_E01_SE01_SH{sh:02d}.mp4"
    for sh in range(1, 7)
]

TASK_DEPARTMENT_MAP = {
    "Storyboard": "Storyboard",
    "Layout": "Layout",
    "Animation": "Animation",
    "Rendering": "Rendering",
    "Compositing": "Compositing",
}


def get_artist_for_task(task_type):
    """Pick an artist from the pre-built department index.

    This used to issue one `get_person(relations=True)` per artist plus one
    `get_department()` per department id, on every single task — roughly
    24,000 HTTP requests for a 250-task run. It is now a dict lookup.
    """
    department_name = TASK_DEPARTMENT_MAP.get(task_type["name"])
    candidates = _artists_by_department.get(department_name)
    return random.choice(candidates) if candidates else random.choice(artists)


def generateTask(shot, task_type, task_status, c):
    artist = get_artist_for_task(task_type)

    # Assign at creation time instead of a follow-up PUT to /actions/.../assign.
    task = gazu.task.new_task(
        shot, task_type, assignees=[artist["id"]], client=c
    )

    shot_offset = timedelta(days=_shot_index(shot["name"]) * SHOT_INTERVAL_DAYS)

    schedule = TASK_SCHEDULE.get(task_type["name"])
    if schedule:
        start = PROJECT_START + shot_offset + timedelta(days=schedule["start_offset"])
        due = start + timedelta(days=schedule["duration"])
        task["start_date"] = start.strftime("%Y-%m-%d")
        task["real_start_date"] = task["start_date"]
        task["due_date"] = due.strftime("%Y-%m-%d")
        task["created_at"] = start.strftime("%Y-%m-%d")
        task["updated_at"] = due.strftime("%Y-%m-%d")
        task["last_comment_date"] = due.strftime("%Y-%m-%d")
        task["estimation"] = schedule["duration"] * 480

        gazu.task.update_task(task, client=c)
    else:
        start = PROJECT_START + shot_offset
        due = start + timedelta(days=30)

    # ── Timesheet generation ──────────────────────────────────────────────────
    _generate_timesheets(task, artist, start, due, c)
    # ─────────────────────────────────────────────────────────────────────────

    timestamp = _task_datetime(start, due, 0.0, jitter_minutes=60)

    # All tasks start at TODO
    comment = gazu.task.add_comment(
        task, todo, "Task created", created_at=timestamp, client=c
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment, client=c)

    if task_status == todo:
        return

    timestamp = _task_datetime(start, due, 0.25, jitter_minutes=120)
    # TODO → WIP
    comment = gazu.task.add_comment(
        task, wip, "Started work", created_at=timestamp, client=c
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment, client=c)

    if task_status == wip:
        return

    # ── Resolve preview file path ─────────────────────────────────────────────
    task_name = task_type["name"]
    shot_index = _shot_index(shot["name"])
    preview_path = None

    if WITH_PREVIEWS:
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
        task, wfa, "Ready for approval", created_at=timestamp, client=c
    )
    wfa_comment["updated_at"] = timestamp
    gazu.task.update_comment(wfa_comment, client=c)

    if preview_path:
        preview_file = gazu.task.add_preview(task, wfa_comment, preview_path, client=c)
        gazu.task.set_main_preview(preview_file, client=c)

    if task_status == wfa:
        return

    timestamp = _task_datetime(start, due, 0.85, jitter_minutes=60)
    # WFA → Retake  ← frontier is retake, stop here
    if task_status == retake:
        comment = gazu.task.add_comment(
            task, retake, "Changes requested", created_at=timestamp, client=c
        )
        comment["updated_at"] = timestamp
        gazu.task.update_comment(comment, client=c)
        return

    timestamp = _task_datetime(start, due, 1.0, jitter_minutes=0)
    # WFA → Done
    comment = gazu.task.add_comment(
        task, done, "Approved", created_at=timestamp, client=c
    )
    comment["updated_at"] = timestamp
    gazu.task.update_comment(comment, client=c)

    # No re-fetch needed: `task` is already the current representation.
    task["done_date"] = timestamp
    gazu.task.update_task(task, client=c)


def _generate_timesheets(task, artist, start: datetime, due: datetime, c) -> None:
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
        date_str = work_date.strftime("%Y-%m-%d")
        budget_key = (artist_id, date_str)

        is_crunch = random.random() < 0.10

        if is_crunch:
            # Crunch: 8 h 30 min – 12 h
            desired = random.randint(510, 720)
        else:
            # Normal: 6–8 h with a soft bell around 7 h
            raw = random.gauss(mu=420, sigma=40)     # mean 7 h, σ 40 min
            desired = int(max(360, min(480, raw)))   # clamp to [6 h, 8 h]

        # Reserve the minutes atomically: read-modify-write must be a single
        # critical section or concurrent tasks would both see the same
        # "remaining" figure and push the artist past MAX_DAILY_MINUTES.
        with _budget_lock:
            already_logged = _artist_day_budget.get(budget_key, 0)
            remaining_budget = MAX_DAILY_MINUTES - already_logged
            if remaining_budget <= 0:
                # Artist is fully booked for this day — skip entirely.
                continue
            duration = min(desired, remaining_budget)
            _artist_day_budget[budget_key] = already_logged + duration

        gazu.task.set_time_spent(task, artist, date_str, duration, client=c)


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
    frontier_status = random.choices([wip, wfa, retake], weights=[50, 40, 10])[0]

    statuses = {}
    for i, name in enumerate(PIPELINE_ORDER):
        if i < frontier_idx:
            statuses[name] = done
        elif i == frontier_idx:
            statuses[name] = frontier_status
        else:
            statuses[name] = todo
    return statuses


def _do_shot(shot, task_types):
    """Generate the whole pipeline for one shot, on this thread's client."""
    c = client()
    cascade = _shot_status_cascade(shot)
    for task_type in task_types:
        generateTask(shot, task_type, cascade[task_type["name"]], c)


def generateTasks():
    storyboard = gazu.task.get_task_type_by_name("Storyboard")
    layout = gazu.task.get_task_type_by_name("Layout")
    animation = gazu.task.get_task_type_by_name("Animation")
    render = gazu.task.get_task_type_by_name("Rendering")
    compositing = gazu.task.get_task_type_by_name("Compositing")

    task_types = [storyboard, layout, animation, render, compositing]

    # Shots are independent of one another, so they parallelize cleanly.
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_do_shot, shot, task_types): shot for shot in shots}
        for i, future in enumerate(as_completed(futures), 1):
            shot = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Shot {shot['name']} failed: {exc}")
            if i % 10 == 0 or i == len(shots):
                print(f"  … {i}/{len(shots)} shots done")


def generateBudget():
    for i in range(len(projects)):
        project = projects[i]
        budget = gazu.project.create_budget(
            project,
            "Production Budget",
            "Labor, hardware, and license costs.",
            "USD",
            PROJECT_START,
            PROJECT_START + timedelta(days=180),
            2000000,
        )

        # Department ids were captured at creation time, so no per-person
        # get_person(relations=True) round-trip is needed here.
        for person in persons:
            department_id = _person_department_id.get(person["id"])
            if not department_id:
                continue

            gazu.client.post(
                f"data/projects/{project['id']}/budgets/{budget['id']}/entries",
                {
                    "budget_id": budget["id"],
                    "department_id": department_id,
                    "person_id": person["id"],
                    "start_date": PROJECT_START,
                    "months_duration": "6",
                    "daily_salary": person.get("daily_salary", "500"),
                    "position": person.get("position", "artist"),
                    "seniority": "mid",
                },
            )


if __name__ == "__main__":
    started = datetime.now()
    try:
        print("Generating people…")
        generatePeople()
        print("Generating productions…")
        generateProductions(1)
        generateAssets()
        generateEpisodes(1)
        generateSequences(1)
        generateShots(50)
        print(f"Generating tasks for {len(shots)} shots on {WORKERS} threads…")
        generateTasks()
        print("Generating budget…")
        generateBudget()
    finally:
        _cleanup_avatar_pool()

    print(f"Done in {datetime.now() - started}.")