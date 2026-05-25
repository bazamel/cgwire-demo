import os
import random
import gazu
from datetime import date, datetime, timedelta
from faker import Faker
fake = Faker()

gazu.set_host("http://localhost/api")
gazu.log_in("admin@example.com", "mysecretpassword")

person_objects = []
projects = []
episodes = []
sequences = []
shots = []
assets = []
tasks = []

def generatePeople():
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

PROJECT_START = datetime(2024, 3, 1)

def generateTask(shot, task_type):
    task = gazu.task.new_task(shot, task_type)

    schedule = TASK_SCHEDULE.get(task_type["name"])
    if schedule:
        start = PROJECT_START + timedelta(days=schedule["start_offset"])
        due   = start + timedelta(days=schedule["duration"])
        task["start_date"] = start.strftime("%Y-%m-%d")
        task["due_date"]   = due.strftime("%Y-%m-%d")
        gazu.task.update_task(task)

def generateTasks():
    storyboard   = gazu.task.get_task_type_by_name("Storyboard")
    layout       = gazu.task.get_task_type_by_name("Layout")
    animation    = gazu.task.get_task_type_by_name("Animation")
    render       = gazu.task.get_task_type_by_name("Rendering")
    compositing  = gazu.task.get_task_type_by_name("Compositing")

    for shot in shots:
        generateTask(shot, storyboard)
        generateTask(shot, layout)
        generateTask(shot, animation)
        generateTask(shot, render)
        generateTask(shot, compositing)


generatePeople()
generateProductions(1)
generateAssets()
generateEpisodes(5)
generateSequences(5)
generateShots(5)
generateTasks()