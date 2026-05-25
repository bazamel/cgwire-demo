"""
fixtures/people.py
------------------
Functions for creating and configuring people and departments.
"""

import gazu


def setup_admin(cfg: dict) -> dict:
    """
    Update the admin account display name and avatar.

    Parameters
    ----------
    cfg : dict
        The ADMIN_DISPLAY dict from config (keys: first_name, last_name,
        full_name, avatar, email).

    Returns
    -------
    dict  The updated admin person object.
    """
    admin = gazu.person.get_person_by_email(cfg["email"])
    gazu.person.set_avatar(admin, cfg["avatar"])
    gazu.person.update_person({
        "id":         admin["id"],
        "full_name":  cfg["full_name"],
        "first_name": cfg["first_name"],
        "last_name":  cfg["last_name"],
    })
    return admin


def get_or_create_department(name: str) -> dict:
    """Return an existing department or create it if absent."""
    dept = gazu.person.get_department_by_name(name)
    if dept is None:
        dept = gazu.person.new_department(name)
    return dept


def create_people(people_cfg: list[dict], department: dict) -> dict[str, dict]:
    """
    Create all people from config and assign them to *department*.

    Parameters
    ----------
    people_cfg  : list of person config dicts (see config.PEOPLE)
    department  : department object to add everyone to

    Returns
    -------
    dict mapping "FirstName LastName" → person object
    """
    person_objects: dict[str, dict] = {}

    for cfg in people_cfg:
        person = gazu.person.new_person(
            cfg["first_name"],
            cfg["last_name"],
            cfg["email"],
            cfg.get("phone", ""),
            cfg.get("role", "user"),
        )
        if cfg.get("avatar"):
            gazu.person.set_avatar(person, cfg["avatar"])

        gazu.person.add_person_to_department(person, department)
        full_name = f"{cfg['first_name']} {cfg['last_name']}".strip()
        person_objects[full_name] = person

    return person_objects