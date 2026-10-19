"""Hand-written documentation of the mario events, rendered into the dataset README.

The reference itself is ``reference.md``, next to this file.
"""

import os.path as op

#: Why a vocabulary entry produces no row in the dataset. Entries absent from here that
#: have zero rows are reported as "never occurred". Keep this honest: "not implemented"
#: means the pipeline has no detector for it.
NOT_EMITTED = {
    "PlayerDied/Timeout": "implemented (death routine with the timer at 0); no "
                          "subject ever ran out of time",
    "EnemyAttack/{enemy_type}": "not implemented (no verified RAM signal)",
    "ProjectileOnScreen/{projectile_type}": "implemented for Bowser's flames (id "
                                            "0x15) but the flame never passes the "
                                            "visibility test; not yet resolved",
    "ShellStartedMoving": "not implemented for SMB1",
    "CheckpointReached": "deliberately not emitted: `HalfwayPage` is written at a "
                         "death past the midpoint, not at the crossing",
    "LevelRestarted": "not applicable: an SMB1 repetition spans all its lives, and "
                      "each restart is a `Screen/LevelIntro` row",
    "Action/Start": "never pressed",
    "Action/Select": "never pressed",
}


#: How each event is read from the RAM and how it was validated, in Markdown. Embedded in
#: the README and in the common event reference.
with open(op.join(op.dirname(__file__), "reference.md")) as _handle:
    REFERENCE = _handle.read()
