"""RAM invariants specific to Super Mario Bros. (NES), run on every repetition after the shared ones.

Like the shared checks, each one recomputes its quantity straight from
``_variables.json`` rather than calling the generator.
"""

from __future__ import annotations

import collections

#: Shortest title card observed (86 frames on the NES, 79 on the SNES); the black screen
#: between areas is 24 frames on the NES and the task-1 stretch of a pipe 35-42 frames on
#: the SNES, so a length threshold separates the two by a different route than the
#: generator's "at the start or after a death" rule.
INTRO_MIN_FRAMES = 60


def check_repetition(events, repvars, summary, path, report) -> None:
    """SMB1 title cards, recounted by length rather than by context: the engine-0
    stretches long enough to be the card."""
    counts = collections.Counter(events["trial_type"].astype(str))
    series = [v == 0 for v in repvars.get("player_state", [])]
    long_runs = 0
    run = 0
    for v in series + [False]:
        if v:
            run += 1
        else:
            long_runs += run >= INTRO_MIN_FRAMES
            run = 0
    intros = counts.get("Screen/LevelIntro", 0)
    if intros != long_runs:
        report.add("V1", "Screen/LevelIntro count disagrees with the title-card "
                         "stretches", path,
                   f"{long_runs} stretch(es) >= {INTRO_MIN_FRAMES} frames, "
                   f"{intros} LevelIntro rows", "warning")
