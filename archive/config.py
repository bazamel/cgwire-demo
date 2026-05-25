"""
fixtures/config.py
------------------
Central configuration for the fixture generator.
Edit these dicts/lists to control exactly what gets created.
"""

from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
KITSU_HOST     = "http://localhost/api"
ADMIN_EMAIL    = "admin@example.com"
ADMIN_PASSWORD = "mysecretpassword"

ADMIN_DISPLAY = {
    "first_name": "Kitsu",
    "last_name":  "",
    "full_name":  "Kitsu",
    "avatar":     "fixtures/fake_user/kitsu.png",
}

# ---------------------------------------------------------------------------
# People
# ---------------------------------------------------------------------------
PEOPLE = [
    {
        "first_name": "Alicia",  "last_name": "Cooper",
        "email": "alicia@cg-wire.com",  "phone": "+33 6 82 38 19 08",
        "role": "user",  "avatar": "fixtures/fake_user/alicia.png",
    },
    {
        "first_name": "Michael", "last_name": "Byrd",
        "email": "michael@cg-wire.com", "phone": "+33 6 32 45 12 45",
        "role": "user",  "avatar": "fixtures/fake_user/michael.png",
    },
    {
        "first_name": "Ann",     "last_name": "Kennedy",
        "email": "ann@cg-wire.com",     "phone": "+33 6 32 45 12 45",
        "role": "user",  "avatar": "fixtures/fake_user/ann.png",
    },
    {
        "first_name": "Brennan", "last_name": "Mason",
        "email": "brennan@cg-wire.com", "phone": "+33 6 43 42 13 21",
        "role": "user",  "avatar": "fixtures/fake_user/brennan.png",
    },
    {
        "first_name": "David",   "last_name": "Penna",
        "email": "david@cg-wire.com",   "phone": "+33 6 08 98 92 12",
        "role": "user",  "avatar": "fixtures/fake_user/david.png",
    },
    {
        "first_name": "Rachel",  "last_name": "Shelton",
        "email": "rachel@cg-wire.com",  "phone": "+33 6 92 38 91 23",
        "role": "user",  "avatar": "fixtures/fake_user/rachel.png",
    },
    {
        "first_name": "Frank",   "last_name": "Rousseau",
        "email": "frank@cg-wire.com",   "phone": "+33 6 22 18 13 88",
        "role": "admin", "avatar": "fixtures/fake_user/frank.png",
    },
]

# Department name that all people above are assigned to
DEFAULT_DEPARTMENT = "Animation"

# ---------------------------------------------------------------------------
# Productions
# ---------------------------------------------------------------------------
# production_type: "short" | "movie" | "tvshow"
PRODUCTIONS = [
    {
        "name":            "Big Buck Bunny",
        "production_type": "short",
        "thumbnail":       None,
    },
    {
        "name":            "Agent 327",
        "production_type": "short",
        "thumbnail":       None,
    },
    {
        "name":            "Caminandes",
        "production_type": "tvshow",
        "thumbnail":       "fixtures/v1.png",
        "assets": [
            ("Characters",   "Lama",       "fixtures/th_assets/lama.png"),
            ("Characters",   "Oti",        "fixtures/th_assets/ep01/oti.png"),
            ("Characters",   "Pingoo",     "fixtures/th_assets/ep01/pingoo.png"),
            ("Environment",  "Mine",       "fixtures/th_assets/ep01/mine.png"),
            ("Environment",  "Pool",       "fixtures/th_assets/ep01/pool.png"),
            ("Environment",  "Railroad",   "fixtures/th_assets/ep01/railroad.jpg"),
            ("Environment",  "Oil Machine","fixtures/th_assets/ep01/oil_machine.png"),
            ("FX",           "Smoke",      "fixtures/th_assets/ep01/smoke.png"),
            ("FX",           "Wind",       "fixtures/th_assets/ep01/wind.png"),
            ("Props",        "Berry",      "fixtures/th_assets/ep01/berry.png"),
            ("Props",        "Flower",     "fixtures/th_assets/ep01/flower.png"),
            ("Props",        "Mine Cart",  "fixtures/th_assets/ep01/cart.png"),
            ("Props",        "Train",      "fixtures/th_assets/ep01/train.png"),
        ],

        # ---- Episodes / sequences / shots ----------------------------------
        # Each episode dict has a name and a list of sequences.
        # Each sequence has a name and a list of shot names.
        # nb_frames is picked randomly from (min, max) if not set explicitly.
        "episodes": [
            {
                "name": "E01",
                "sequences": [
                    {"name": "SE01", "shots": [f"SH{i:03d}" for i in range(1, 12)]},
                    {"name": "SE02", "shots": [f"SH{i:03d}" for i in range(1, 12)]},
                    {"name": "SE03", "shots": [f"SH{i:03d}" for i in range(1, 12)]},
                ],
            },
            {
                "name": "E02",
                "sequences": [
                    {"name": "SE01", "shots": [f"SH{i:03d}" for i in range(1, 4)]},
                    {"name": "SE02", "shots": [f"SH{i:03d}" for i in range(1, 4)]},
                ],
            },
            {
                "name": "E03",
                "sequences": [
                    {"name": "SE01", "shots": [f"SH{i:03d}" for i in range(1, 8)]},
                    {"name": "SE02", "shots": [f"SH{i:03d}" for i in range(1, 8)]},
                    {"name": "SE03", "shots": [f"SH{i:03d}" for i in range(1, 8)]},
                ],
            },
        ],

        # ---- Shot animation assignments ------------------------------------
        # Maps sequence index (0-based) to the full name of the animator.
        "sequence_animators": {
            0: "Alicia Cooper",
            1: "Brennan Mason",
            2: "David Penna",
        },

        # ---- Casting -------------------------------------------------------
        # Applied to the first N shots (by flat shot index).
        # asset_name → nb_occurences
        "casting_shots": 4,          # how many shots get this casting
        "casting": [
            {"asset_name": "Lama",   "nb_occurences": 1},
            {"asset_name": "Pingoo", "nb_occurences": 1},
            {"asset_name": "Berry",  "nb_occurences": 2},
        ],

        # ---- Preview file roots --------------------------------------------
        # Keys are task-type names; values are glob-style roots.
        # The loader will fall back gracefully if files are absent.
        "preview_roots": {
            "Storyboard":   "fixtures/th_shots/ep01/SB",
            "Animation":    "fixtures/th_shots/ep01/Anim",
            "Rendering":    "fixtures/th_shots/ep01/render",
        },
    },
]

# ---------------------------------------------------------------------------
# Asset types to ensure exist
# ---------------------------------------------------------------------------
ASSET_TYPES = ["Characters", "Props", "Environment", "FX"]

# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
def first_monday_three_months_ago(from_date: date = None) -> date:
    if from_date is None:
        from_date = date.today()
    # Go back ~3 months
    month = from_date.month - 3
    year = from_date.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    target = from_date.replace(year=year, month=month)
    # Roll forward to the next Monday (or stay if already Monday)
    days_ahead = (7 - target.weekday()) % 7
    return target + timedelta(days=days_ahead)
    
PROJECT_START        = first_monday_three_months_ago()
ASSET_TASK_DURATION  = 5                  # working days
SHOT_TASK_DURATION   = 3                  # working days

# ---------------------------------------------------------------------------
# Frame count range for shots (when not specified explicitly)
# ---------------------------------------------------------------------------
FRAMES_MIN = 20
FRAMES_MAX = 90