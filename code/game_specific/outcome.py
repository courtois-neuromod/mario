"""How a repetition ended, decided from the game engine rather than from heuristics.

The labels, shared by the CNeuroMod videogame datasets:

    cleared
    failed/killed, failed/fall, failed/timeout
    incomplete/warp, incomplete/interrupted
    unknown

**mario / mariostars.** The shipped logic tested ``jump_airborne == 3``. That value is
Player_State $001D, which is the flagpole slide *and* the vine climb, so a W4-2 warp
taken up the vine was labelled ``cleared``. It also never fires on castle levels, where
the level ends at an axe rather than a flagpole. Both are replaced by the engine's own
``PlayerEndLevel`` routine (``GameEngineSubroutine`` == 5), which fires on every kind of
level ending and on nothing else.

"""

from __future__ import annotations

from typing import Optional, Sequence

#: GameEngineSubroutine / player_action_state values (shared by SMB1 on NES and SNES).
ENGINE_FLAGPOLE_SLIDE = 4
ENGINE_END_LEVEL = 5
ENGINE_LOSE_LIFE = 6
ENGINE_DEATH = 11



def _first_transition(series: Sequence, value) -> Optional[int]:
    for index in range(1, len(series)):
        if series[index] == value and series[index - 1] != value:
            return index
    return None


def _changed(series) -> bool:
    return bool(series) and len(series) > 1 and any(
        series[i] != series[i - 1] for i in range(1, len(series)))


def _last_change(series) -> Optional[int]:
    """Frame of the last change in a series, or None."""
    for index in range(len(series) - 1, 0, -1):
        if series[index] != series[index - 1]:
            return index
    return None




def smb1_outcome(repvars: dict, engine_var: str = "player_state",
                 timer_var: str = "time") -> str:
    """Outcome for Super Mario Bros, on either port.

    The label describes how the repetition *ended*, so the three possible terminal
    events -- reaching the end of the level, warping out, and dying -- are all located
    and the **latest** one wins. Ordering them by time rather than by precedence matters
    in both directions:

    * a player can climb a vine (which the shipped logic mistook for a flagpole slide)
      and then lose their last life, which is a failure, not a clear;
    * a player can lose a life early and then take the W4-2 warp pipe, which is a warp
      exit, not a death.

    Each death is attributed by looking at the engine between the previous death and this
    one: if the death routine (``GameEngineSubroutine`` == 11) ran, the player was killed
    by something; if the engine went straight to losing a life (== 6) without it, the
    player dropped off the bottom of the screen.

    Args:
        engine_var: ``player_state`` on the NES, ``player_action_state`` on the SNES.
            Both hold the same GameEngineSubroutine enumeration.
    """
    try:
        engine = repvars.get(engine_var) or []
        lives = repvars["lives"]
        n = len(engine)

        # --- candidate terminal events, each with the frame it happened on ------------

        # The engine's own end-of-level routine. Fires on flagpole and castle levels
        # alike, unlike the flagpole-slide test, which also fires on a vine climb.
        end_frame = _first_transition(engine, ENGINE_END_LEVEL)

        # A warp-zone exit moves the player to another world or area.
        world = repvars.get("world") or repvars.get("current_world") or []
        area = repvars.get("area") or repvars.get("current_level") or []
        warp_frame = max(
            (f for f in (_last_change(world), _last_change(area)) if f is not None),
            default=None)

        deaths = [i for i in range(1, len(lives)) if lives[i] < lives[i - 1]]
        if not deaths:
            deaths = [i for i in range(1, n)
                      if engine[i] == ENGINE_LOSE_LIFE and engine[i - 1] != ENGINE_LOSE_LIFE]
        death_frame = deaths[-1] if deaths else None

        # --- decide -----------------------------------------------------------------
        # Completing a level also advances the world index, so a world change is only a
        # warp when the level never ended: `end_frame` takes precedence over it. Among
        # the remaining two, order matters -- a player can lose a life early and then
        # take the W4-2 warp pipe, which is a warp exit rather than a death.
        if end_frame is not None:
            return "cleared"

        if warp_frame is not None and (death_frame is None or warp_frame > death_frame):
            return "incomplete/warp"

        if death_frame is None:
            return "incomplete/interrupted"
        frame = death_frame

        # A death: attribute it from the engine between the previous death and this one.
        previous = deaths[-2] if len(deaths) > 1 else -1
        span = engine[previous + 1:frame + 1]
        routine_frame = None
        for offset, value in enumerate(span):
            if value == ENGINE_DEATH:
                routine_frame = previous + 1 + offset
                break
        if routine_frame is None:
            return "failed/fall"

        timer = repvars.get(timer_var) or []
        if timer:
            window = timer[max(0, routine_frame - 120):routine_frame + 1]
            if window and all(t == 0 for t in window):
                return "failed/timeout"
        return "failed/killed"
    except (KeyError, IndexError, TypeError):
        return "unknown"




def outcome(repvars: dict) -> str:
    """Outcome of one repetition."""
    return smb1_outcome(repvars, "player_state", "time")
