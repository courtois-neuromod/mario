"""What :mod:`videogames_utils.events` needs to know about Super Mario Bros. (NES).

See :class:`videogames_utils.events.game.Game`.
"""

from videogames_utils.events.game import Game

from . import docs, generator, outcome, ram, validation
from .vocabulary import VOCABULARY


GAME = Game(
    task="mario",
    name="Super Mario Bros. (NES)",
    game_id="SuperMarioBros-Nes",
    frame_rate=generator.FRAME_RATE,
    vocabulary=VOCABULARY,
    generate=generator.generate,
    outcome=outcome.outcome,
    form_states=frozenset({"PlayerState/Small", "PlayerState/Super",
                           "PlayerState/Fire"}),
    form_var="player_status",
    state_timers=(("star_timer", "PlayerState/Star"),
                  ("injury_timer", "PlayerState/HitRecovery")),
    coin_var="coins",
    check_repetition=validation.check_repetition,
    reference=docs.REFERENCE,
    not_emitted=docs.NOT_EMITTED,
    golden_sessions=[("sub-01", "ses-001")],
    ram_candidates=ram.SMB1_CANDIDATES,
)
