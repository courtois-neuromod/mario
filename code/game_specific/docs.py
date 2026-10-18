"""Hand-written documentation of the mario events, rendered into the dataset README."""

#: Why a vocabulary entry produces no row in the dataset. Entries absent from here that
#: have zero rows are reported as "never occurred". Keep this honest: "not implemented"
#: means the pipeline has no detector for it.
NOT_EMITTED = {
    "PlayerDied/Timeout": "implemented (death routine with the timer at 0); no "
                          "subject ever ran out of time",
    "ItemCollected/Powerup": "not implemented; the pickup is the first frame of the "
                             "`PlayerState/Super`, `Fire` or `Star` row it starts (a "
                             "1-up is `LifeGained`)",
    "EnemyAttack/{enemy_type}": "not implemented (no verified RAM signal)",
    "ProjectileOnScreen/{projectile_type}": "implemented for Bowser's flames (id "
                                            "0x15) but the flame never passes the "
                                            "visibility test; not yet resolved",
    "ShellStartedMoving": "not implemented for SMB1",
    "CheckpointReached": "deliberately not emitted: `HalfwayPage` is written at a "
                         "death past the midpoint, not at the crossing",
    "LevelRestarted": "not applicable: an SMB1 repetition spans all its lives, and "
                      "each restart is a `Screen/LevelIntro` row",
    "Action/Other": "the NES pad has no extra buttons",
    "Action/Start": "never pressed",
    "Action/Select": "never pressed",
}

#: Accuracy notes, in Markdown. Reviewed by hand when the generator changes.
NOTES = """\
- `PlayerState/*` rows are read straight from the RAM: `PlayerStatus` ($0756,
  `player_status`) for the form, which the game writes on the very frame a mushroom or
  flower is collected or a hit lands; `StarInvincibleTimer` ($079F, `star_timer`) for
  `Star`; and `InjuryTimer` ($079E, `injury_timer`) for `HitRecovery`, the ~3.7 s after
  a hit during which enemy contact is ignored. Form rows (Small included) exist only on
  the frames where the player is alive in the level, so they are cut at a death and
  resume once the title card has gone. Validation recounts every row from the same
  series by a different route.
- `Screen/*` rows come from the engine state (`GameEngineSubroutine`, $000E,
  `player_state`): 0/1/2/3/7 are transitions, 4/5 the end-of-level sequence, 11/6 the
  death, everything else play. A transition block at the start of the repetition or
  right after a death is the title card (`Screen/LevelIntro`). Every boundary was
  checked on rendered emulator frames; a fall death is dated from `Player_Y_HighPos`
  leaving 1 (exact).
- Enemy visibility uses the game's own `EnemyOffscrBitsMasked` ($03D8). Validated against
  independently computed screen-relative positions: when it is zero the enemy is inside
  the visible band on 97.5-98.9% of frames, when non-zero on 0.0-1.5%. Piranha Plants
  count only while out of their pipe (from the per-slot Y), Bullet Bills only while in
  flight (the cannon shares their id and does not move).
- Enemy types come from `Enemy_ID` ($0016) decoded through the object table in
  1wErt3r's SMB disassembly. Cross-checked against mariostars on the levels played on
  both consoles.
- `LevelCompleted` uses the engine's `PlayerEndLevel` routine, so it also fires on
  castle levels where there is no flagpole. `LevelExited/Warp` is detected from the
  world/area index changing while the level never ended.
- Recordings end at the life loss on the last life, so there is no game-over screen in
  this dataset. START is never pressed, so there is no pause.
"""
