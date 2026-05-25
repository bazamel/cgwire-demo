"""
fixtures/scheduling.py
----------------------
Working-day arithmetic and task scheduling helpers.

Scheduling rules
~~~~~~~~~~~~~~~~
* Tasks are spread realistically across a 6-month (≈130 working-day) window.
* Each task gets an individual duration drawn from a realistic range for its
  type rather than a flat global value.
* 10 % of tasks receive a **retake**: a second task of the same type is
  appended immediately after the original, consuming extra working days.
* 10 % of tasks are flagged as **late**: their due-date is pulled back so it
  falls before TODAY, simulating schedule slippage.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from typing import Optional

import gazu


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Fraction of tasks that get a retake / are flagged late.
RETAKE_RATE = 0.10
LATE_RATE   = 0.10

# Realistic working-day durations per task type (min, max).
DURATION_RANGES: dict[str, tuple[int, int]] = {
    "Modeling":    (4, 8),
    "Rigging":     (3, 6),
    "Storyboard":  (2, 4),
    "Animation":   (5, 10),
    "Rendering":   (3, 6),
    "Compositing": (3, 5),
    # Retake tasks are shorter – a correction, not a full redo.
    "_retake":     (2, 4),
}

# Gazu status names – adjust to match your project's workflow statuses.
STATUS_LATE    = "Late"       # or whatever your retake status is named
STATUS_RETAKE  = "Retake"


# ---------------------------------------------------------------------------
# Seeded RNG (swap for random.Random() without a seed in production)
# ---------------------------------------------------------------------------

_rng = random.Random(42)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def add_working_days(start: date, days: int) -> date:
    """Advance *start* by *days* Mon–Fri working days."""
    current = start
    added   = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


def date_str(d: date) -> str:
    return d.isoformat()


def _duration(task_type_name: str) -> int:
    """Return a random realistic duration (working days) for *task_type_name*."""
    lo, hi = DURATION_RANGES.get(task_type_name, (3, 6))
    return _rng.randint(lo, hi)


# ---------------------------------------------------------------------------
# Retake / late helpers
# ---------------------------------------------------------------------------

def _maybe_retake(
    entity,
    task_type: dict,
    type_name: str,
    due: date,
) -> date:
    """
    With probability RETAKE_RATE create a retake task immediately after *due*.
    Returns the new cursor (day after retake due, or original *due* if no retake).
    """
    if _rng.random() >= RETAKE_RATE:
        return due

    rt_dur   = _rng.randint(*DURATION_RANGES["_retake"])
    rt_start = add_working_days(due, 1)
    rt_due   = add_working_days(rt_start, rt_dur)

    retake_task = gazu.task.new_task(entity, task_type, name=f"{type_name} – Retake")
    retake_task.start_date = date_str(rt_start)
    retake_task.due_date   = date_str(rt_due)
    gazu.task.update_task(retake_task)

    # Mark with retake status if the project uses it.
    try:
        retake_status = gazu.task.get_task_status_by_name(STATUS_RETAKE)
        gazu.task.update_task(retake_task, {"task_status_id": retake_status["id"]})
    except Exception:
        pass  # status may not exist in every project

    return rt_due   # cursor advances past the retake


def _apply_late_flag(task: dict, start: date, due: date, today: date) -> None:
    """
    With probability LATE_RATE, pull the task's due_date back so it is
    before *today*, simulating a missed deadline.
    """
    if _rng.random() >= LATE_RATE:
        return

    # Push due date 1–5 working days before today.
    lag      = _rng.randint(1, 5)
    late_due = add_working_days(today, -lag)

    # Clamp: late due must still be after start.
    if late_due <= start:
        late_due = add_working_days(start, 1)

    gazu.task.update_task(task, {"due_date": date_str(late_due)})

    try:
        late_status = gazu.task.get_task_status_by_name(STATUS_LATE)
        gazu.task.update_task(task, {"task_status_id": late_status["id"]})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Task creation
# ---------------------------------------------------------------------------

def schedule_asset_tasks(
    assets: list[dict],
    modeling_type: dict,
    rigging_type: dict,
    project_start: date,
    task_duration: int,           # kept for API compatibility; used as fallback
    today: Optional[date] = None,
) -> date:
    """
    Create Modeling + Rigging tasks for every asset, scheduled sequentially
    across the 6-month window.

    *today* is used to flag late tasks; defaults to ``date.today()``.

    Returns the *cursor* date (first free working day after all asset tasks).
    """
    today   = today or date.today()
    cursor  = project_start

    for asset in assets:
        # --- Modeling ---
        m_dur   = _duration("Modeling")
        m_start = cursor
        m_due   = add_working_days(m_start, m_dur)

        m_task = gazu.task.new_task(asset, modeling_type)
        m_task.start_date = date_str(m_start)
        m_task.due_date   = date_str(m_due)
        gazu.task.update_task(m_task)
        _apply_late_flag(m_task, m_start, m_due, today)
        m_due = _maybe_retake(asset, modeling_type, "Modeling", m_due)

        # --- Rigging ---
        r_dur   = _duration("Rigging")
        r_start = add_working_days(m_due, 1)
        r_due   = add_working_days(r_start, r_dur)

        r_task = gazu.task.new_task(asset, rigging_type)
        r_task.start_date = date_str(r_start)
        r_task.due_date   = date_str(r_due)
        gazu.task.update_task(r_task)
        _apply_late_flag(r_task, r_start, r_due, today)
        r_due = _maybe_retake(asset, rigging_type, "Rigging", r_due)

        cursor = add_working_days(r_due, 1)

    return cursor


def schedule_shot_tasks(
    shots: list[dict],
    sequences: list[dict],
    task_types: dict[str, dict],          # name → task-type object
    sequence_animators: dict[int, dict],  # seq-index → person object
    start_cursor: date,
    task_duration: int,                   # kept for API compatibility; used as fallback
    today: Optional[date] = None,
) -> date:
    """
    Create Storyboard → Animation → Rendering → Compositing tasks for every
    shot, assigning animators by sequence index.

    10 % of tasks receive a retake; 10 % are flagged as late.

    Returns the cursor date after all shot tasks.
    """
    today = today or date.today()

    # Build a fast lookup: sequence_id → sequence index.
    seq_id_to_index = {seq["id"]: i for i, seq in enumerate(sequences)}

    storyboard  = task_types["Storyboard"]
    animation   = task_types["Animation"]
    rendering   = task_types["Rendering"]
    compositing = task_types["Compositing"]

    cursor = start_cursor

    for shot in shots:

        # --- Storyboard ---
        sb_dur   = _duration("Storyboard")
        sb_start = cursor
        sb_due   = add_working_days(sb_start, sb_dur)

        sb_task = gazu.task.new_task(shot, storyboard)
        sb_task.start_date = date_str(sb_start)
        sb_task.due_date   = date_str(sb_due)
        gazu.task.update_task(sb_task)
        _apply_late_flag(sb_task, sb_start, sb_due, today)
        sb_due = _maybe_retake(shot, storyboard, "Storyboard", sb_due)

        # --- Animation ---
        anim_dur   = _duration("Animation")
        anim_start = add_working_days(sb_due, 1)
        anim_due   = add_working_days(anim_start, anim_dur)

        anim_task = gazu.task.new_task(shot, animation)
        anim_task.start_date = date_str(anim_start)
        anim_task.due_date   = date_str(anim_due)
        gazu.task.update_task(anim_task)
        _apply_late_flag(anim_task, anim_start, anim_due, today)
        anim_due = _maybe_retake(shot, animation, "Animation", anim_due)

        # Assign animator based on the shot's parent sequence.
        seq_idx = seq_id_to_index.get(shot.get("parent_id"))
        if seq_idx is not None and seq_idx in sequence_animators:
            gazu.task.assign_task(anim_task, sequence_animators[seq_idx])

        # --- Rendering ---
        rend_dur   = _duration("Rendering")
        rend_start = add_working_days(anim_due, 1)
        rend_due   = add_working_days(rend_start, rend_dur)

        rend_task = gazu.task.new_task(shot, rendering)
        rend_task.start_date = date_str(rend_start)
        rend_task.due_date   = date_str(rend_due)
        gazu.task.update_task(rend_task)
        _apply_late_flag(rend_task, rend_start, rend_due, today)
        rend_due = _maybe_retake(shot, rendering, "Rendering", rend_due)

        # --- Compositing ---
        comp_dur   = _duration("Compositing")
        comp_start = add_working_days(rend_due, 1)
        comp_due   = add_working_days(comp_start, comp_dur)

        comp_task = gazu.task.new_task(shot, compositing)
        comp_task.start_date = date_str(comp_start)
        comp_task.due_date   = date_str(comp_due)
        gazu.task.update_task(comp_task)
        _apply_late_flag(comp_task, comp_start, comp_due, today)
        comp_due = _maybe_retake(shot, compositing, "Compositing", comp_due)

        cursor = add_working_days(comp_due, 1)

    return cursor