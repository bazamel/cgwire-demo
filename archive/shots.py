"""
fixtures/shots.py
-----------------
Functions for building the episode → sequence → shot hierarchy.
"""

import random
import gazu


def create_shot_hierarchy(
    project: dict,
    episodes_cfg: list[dict],
    frames_min: int = 20,
    frames_max: int = 90,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Create all episodes, sequences, and shots for *project*.

    Parameters
    ----------
    project      : project object
    episodes_cfg : list of episode config dicts (see config.PRODUCTIONS[n]["episodes"])
    frames_min / frames_max : range for random frame counts

    Returns
    -------
    (episodes, sequences, shots)  – flat lists in creation order
    """
    all_episodes:  list[dict] = []
    all_sequences: list[dict] = []
    all_shots:     list[dict] = []

    for ep_cfg in episodes_cfg:
        episode = gazu.shot.new_episode(project, ep_cfg["name"])
        all_episodes.append(episode)

        for seq_cfg in ep_cfg.get("sequences", []):
            sequence = gazu.shot.new_sequence(project, seq_cfg["name"], episode=episode)
            all_sequences.append(sequence)

            for shot_name in seq_cfg.get("shots", []):
                nb_frames = seq_cfg.get("nb_frames") or random.randrange(
                    frames_min, frames_max, 1
                )
                shot = gazu.shot.new_shot(
                    project, sequence, shot_name, nb_frames=nb_frames
                )
                all_shots.append(shot)

    return all_episodes, all_sequences, all_shots