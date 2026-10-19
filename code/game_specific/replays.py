"""The Super Mario Bros. parts of the replay pipeline (:mod:`videogames_utils.replays`): the
game's own ``_summary.json`` fields and the protocol phases.

The counting functions are those of the former ``code/replays/generate_replays.py``.
"""

from __future__ import annotations

import numpy as np

from .generator import FRAME_RATE


def _calculate_distance_traveled(repetition_variables):
    """Calculate total X distance traveled."""
    start_x = (repetition_variables["xscrollLo"][0] +
               (256 * repetition_variables["xscrollHi"][0]))
    end_x = (repetition_variables["xscrollLo"][-1] +
             (256 * repetition_variables["xscrollHi"][-1]))
    return end_x - start_x


def _count_enemy_kills_for_slot(repetition_variables, slot_idx):
    """Count kills for a specific enemy slot."""
    kill_count = 0
    enemy_key = f"enemy_kill3{slot_idx}"

    for idx, val in enumerate(repetition_variables[enemy_key][:-1]):
        if val in [4, 34, 132]:
            if repetition_variables[enemy_key][idx + 1] != val:
                if slot_idx == 5 and repetition_variables["powerup_yes_no"] == 0:
                    kill_count += 1
                elif slot_idx != 5:
                    kill_count += 1
    return kill_count


def count_kills(repetition_variables):
    """Count total enemies killed during replay."""
    return sum(_count_enemy_kills_for_slot(repetition_variables, i) for i in range(6))


def count_powerups_collected(repetition_variables):
    """Count powerups collected during replay."""
    powerup_count = 0

    for idx, val in enumerate(repetition_variables["player_state"][:-1]):
        if val in [9, 12, 13]:
            if repetition_variables["player_state"][idx + 1] != val:
                powerup_count += 1
    return powerup_count

def _count(events, *trial_types) -> int:
    """Rows of the repetition's events with one of ``trial_types``."""
    return int(events["trial_type"].isin(trial_types).sum()) if len(events) else 0


def hits_taken(events) -> int:
    """Hits that cost a power-up or a life. A fall or a timeout is not a hit."""
    return _count(events, "PlayerDamaged", "PlayerDied/Enemy")


def bricks_smashed(events) -> int:
    """Bricks broken, as in the events (``BlockSmashed``)."""
    return _count(events, "BlockSmashed")


def summary(repvars: dict, events) -> dict:
    """The game's fields of a repetition's ``_summary.json``."""
    duration = len(repvars["score"]) / FRAME_RATE
    distance = _calculate_distance_traveled(repvars)
    return {
        "ScoreGained": repvars["score"][-1] - repvars["score"][0],
        "LivesLost": repvars["lives"][0] - repvars["lives"][-1],
        "HitsTaken": hits_taken(events),
        "EnemiesDefeated": count_kills(repvars),
        "CoinsCollected": repvars["coins"][-1] - repvars["coins"][0],
        "PowerupsCollected": count_powerups_collected(repvars),
        "BricksSmashed": bricks_smashed(events),
        "DistanceTraveled": distance,
        "AverageSpeed": distance / duration,
    }


def phases(repetitions):
    """Discovery while a run plays a single level (levels in game order, repeated),
    practice once runs mix levels (pseudo-random order, one repetition each)."""
    return np.where(repetitions["run_levels"] == 1, "discovery", "practice")
