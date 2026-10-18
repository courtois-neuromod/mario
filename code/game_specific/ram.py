"""RAM variables of Super Mario Bros. (NES): the candidates verified before they were
added to ``stimuli/SuperMarioBros-Nes/data.json``, and the object id tables.

Source: 1wErt3r's SMB disassembly (SMBDIS.ASM), https://gist.github.com/1wErt3r/4048722
"""

from __future__ import annotations

from typing import Dict, List

from videogames_utils.events.ram import Candidate, candidate_array


# --- Super Mario Bros (NES) -------------------------------------------------------
# Enemy object arrays are 6 slots wide. Enemy_ID[5] is already present in the shipped
# data.json under the (misleading) name "powerup_yes_no", Enemy_Flag[0..4] under
# "enemy_drawn15".."enemy_drawn19", and Enemy_State[0..5] under "enemy_kill30".."enemy_kill35".

SMB1_CANDIDATES: List[Candidate] = [
    *candidate_array("enemy_id", 0x16, 6, "|u1", "Enemy_ID", "enemy type per slot"),
    Candidate("enemy_drawn20", 0x14, "|u1", "Enemy_Flag[5]", "6th Enemy_Flag slot"),
    *candidate_array("enemy_x", 0x87, 6, "|u1", "Enemy_X_Position", "screen X per slot"),
    *candidate_array("enemy_y", 0xCF, 6, "|u1", "Enemy_Y_Position", "screen Y per slot"),
    *candidate_array("enemy_pageloc", 0x6E, 6, "|u1", "Enemy_PageLoc",
            "X page per slot; absolute X = pageloc * 256 + enemy_x"),
    *candidate_array("enemy_y_high", 0xB6, 6, "|u1", "Enemy_Y_HighPos",
            "Y page per slot; 1 = within the visible band"),
    # Enemy_OffscreenBits ($03D1) is SCRATCH - it holds the bits of whichever enemy is
    # being processed on this frame, not a per-slot mask (verified empirically: slots 4
    # and 5 never set their bit). The persistent per-slot array is EnemyOffscrBitsMasked.
    *candidate_array("enemy_offscr_masked", 0x03D8, 6, "|u1", "EnemyOffscrBitsMasked",
            "per-slot: non-zero = enemy is offscreen by some amount"),
    *candidate_array("enemy_sprattrib", 0x03C5, 6, "|u1", "Enemy_SprAttrib",
            "per-slot sprite attributes"),
    # PlayerStatus is a single byte, but the shipped data.json declares this same address
    # as "powerstate" with type ">d4" -- a 4-byte BCD read spanning $0756-$0759, so it
    # mixes in the neighbouring death flag at $0757 and reports values like 10000. The
    # shipped generator never reads it, which is why the bug went unnoticed. "powerstate"
    # is left in place (removing it would break anyone reading it); use this instead.
    # Verified: reads 0/1/2 with clean transitions 0->1 on a mushroom, 1->2 on a fire
    # flower and 2->0 on taking damage.
    Candidate("player_status", 0x0756, "|u1", "PlayerStatus",
              "0 small, 1 super, 2 fire -- correctly typed replacement for 'powerstate'"),
    # InjuryTimer is the post-hit invulnerability window. ForceInjury sets it to 8 when a
    # big Mario is hit and InjurePlayer ignores enemy contact while it is non-zero; it
    # counts on the 21-frame interval clock and pauses while the shrink animation halts
    # the timers, so it runs ~220 frames (3.7 s). Verified: non-zero from exactly the
    # engine-10 frame for 223 frames in a w1-2 replay, 8 -> 1.
    Candidate("injury_timer", 0x079E, "|u1", "InjuryTimer",
              "post-hit invulnerability countdown, 8 -> 0 (interval-timer units)"),
    # NOTE: HalfwayPage is written when the player DIES past the level midpoint, to place
    # the respawn, not when the midpoint is crossed. Verified: in a w1-1 replay it is
    # non-zero only during the two death/respawn sequences. It therefore cannot mark
    # CheckpointReached; kept because it records whether a respawn used the checkpoint.
    Candidate("halfway_page", 0x075B, "|u1", "HalfwayPage",
              "respawn page, written at death past the midpoint (NOT a crossing marker)"),
    Candidate("event_music_queue", 0xFC, "|u1", "EventMusicQueue",
              "0x01 death, 0x20 end-of-level, 0x40 time-running-out"),
    Candidate("player_collision_bits", 0x0490, "|u1", "Player_CollisionBits", ""),
    Candidate("enemy_collision_bits", 0x0491, "|u1", "Enemy_CollisionBits", ""),
    Candidate("stomp_chain_counter", 0x0484, "|u1", "StompChainCounter", ""),
    Candidate("enemy_frenzy_buffer", 0x06CB, "|u1", "EnemyFrenzyBuffer",
              "frenzy spawner (Bullet Bill / Cheep-Cheep)"),
    Candidate("frenzy_enemy_timer", 0x078F, "|u1", "FrenzyEnemyTimer", ""),
    Candidate("area_type", 0x074E, "|u1", "AreaType",
              "0 water, 1 ground, 2 underground, 3 castle"),
]



# --------------------------------------------------------------------- decode tables

#: Enemy/object ids for SMB1 ($00-$36), from SMBDIS.ASM: the named constants plus the
#: ``InitEnemyRoutines`` jump table, which covers the whole range including the entries
#: that have no symbolic constant. Ids with neither a constant nor a distinguishing init
#: routine are left as ``Unknown0xNN`` rather than guessed; the validator flags any that
#: actually turn up in the data.
#:
#: Super Mario All-Stars reuses these ids verbatim in ``sprite_number_*`` (verified
#: empirically against mariostars replays: 13=PiranhaPlant, 6=Goomba, 2=BuzzyBeetle,
#: 0=GreenKoopa, 14=GreenParatroopa, 48=FlagpoleFlag, 49=StarFlag).
SMB1_ENEMY_IDS: Dict[int, str] = {
    0x00: "GreenKoopa", 0x01: "Unknown0x01", 0x02: "BuzzyBeetle", 0x03: "RedKoopa",
    0x04: "Unknown0x04", 0x05: "HammerBro", 0x06: "Goomba", 0x07: "Blooper",
    0x08: "BulletBill", 0x09: "Unknown0x09", 0x0A: "GreyCheepCheep",
    0x0B: "RedCheepCheep", 0x0C: "Podoboo", 0x0D: "PiranhaPlant",
    0x0E: "GreenParatroopaJump", 0x0F: "RedParatroopa", 0x10: "GreenParatroopaFly",
    0x11: "Lakitu", 0x12: "Spiny", 0x13: "Unknown0x13", 0x14: "FlyingCheepCheep",
    0x15: "BowserFlame", 0x16: "Fireworks", 0x17: "BulletBillCheepCheepFrenzy",
    0x18: "StopFrenzy", 0x19: "Unknown0x19", 0x1A: "Unknown0x1A",
    0x1B: "ShortFirebar", 0x1C: "ShortFirebar", 0x1D: "ShortFirebar",
    0x1E: "ShortFirebar", 0x1F: "LongFirebar",
    0x20: "Unknown0x20", 0x21: "Unknown0x21", 0x22: "Unknown0x22",
    0x23: "Unknown0x23", 0x24: "BalancePlatform", 0x25: "VerticalPlatform",
    0x26: "LargeLiftUp", 0x27: "LargeLiftDown", 0x28: "HorizontalPlatform",
    0x29: "DropPlatform", 0x2A: "HorizontalPlatform", 0x2B: "PlatformLiftUp",
    0x2C: "PlatformLiftDown", 0x2D: "Bowser", 0x2E: "PowerUpObject",
    0x2F: "VineObject", 0x30: "FlagpoleFlagObject", 0x31: "StarFlagObject",
    0x32: "JumpspringObject", 0x33: "BulletBillCannon", 0x34: "Unknown0x34",
    0x35: "RetainerObject", 0x36: "EndOfEnemyObjects",
}

#: Moving platforms and lifts. They live in enemy slots but are scenery, not enemies.
SMB1_PLATFORM_IDS = frozenset(range(0x24, 0x2D))

#: Items, scenery and end-of-level objects that occupy an enemy slot.
SMB1_ITEM_SCENERY_IDS = frozenset({0x16, 0x2E, 0x2F, 0x30, 0x31, 0x32, 0x35, 0x36})

#: Spawner / control objects that occupy an enemy slot without ever being drawn.
#: They churn through a slot a frame at a time and must not produce Enemy_* events.
SMB1_SPAWNER_IDS = frozenset({0x17, 0x18})

#: The two ids a Bullet Bill can occupy: 0x08 when spawned by a frenzy and 0x33 when
#: fired from a cannon. Both are the same object -- measured over 120 mario replays,
#: runs of either id move at a median 1.5 px/frame, and 0x33 accounts for the large
#: majority (331 flying runs vs 90 for 0x08; on mariostars 283 vs 43). 0x33 was
#: previously classed as a spawner, which discarded most of the Bullet Bills in both
#: datasets outright.
#:
#: The id is shared with the stationary cannon object, which sits in a slot without
#: moving. Where per-slot X is available (NES) a motion test separates them; see
#: ``smb1._is_flying_bullet``.
SMB1_BULLET_IDS = frozenset({0x08, 0x33})

#: SMB1 ids that are projectiles rather than enemies proper. Bullet Bills are NOT here:
#: they are stompable, damage the player on contact, and behave as enemies. Bowser's
#: flame cannot be defeated and stays a projectile.
SMB1_PROJECTILE_IDS = frozenset({0x15})

#: The Piranha Plant, which hides inside its pipe for part of its cycle.
SMB1_PIRANHA_ID = 0x0D

#: Everything that is NOT an enemy for the purposes of Enemy_* events.
SMB1_NON_ENEMY_IDS = (
    SMB1_PLATFORM_IDS | SMB1_ITEM_SCENERY_IDS | SMB1_SPAWNER_IDS | SMB1_PROJECTILE_IDS
)
