Super Mario All-Stars reuses SMB1's object id table verbatim (verified empirically) and
the same engine enumeration, so the `mario` (NES) and `mariostars` (SNES) datasets share
this reference. Where the two ports differ, both variable names are given as
*NES / SNES*.

### The engine state variable

Most Super Mario Bros. events are read from one variable, the game's own statement of
what the player is doing. It is `GameEngineSubroutine` at `$000E`, exposed as
`player_state` on the NES and `player_action_state` on the SNES (Super Mario All-Stars
reuses the same enumeration). Values, from the disassembly's dispatch table:

| value | routine | used for |
|---|---|---|
| 0 | `Entrance_GameTimerSetup` | `Screen/LevelIntro` (the black title card, at a level start or after a life loss) or `Screen/Transition` (the ~24-frame black screen between areas) |
| 1 | `Vine_AutoClimb` | `Screen/Transition` |
| 2 | `SideExitPipeEntry` | `PipeEntered`, `Screen/Transition` |
| 3 | `VerticalPipeEntry` | `PipeEntered`, `Screen/Transition` |
| 4 | `FlagpoleSlide` | `LevelCompleted` (fallback), start of `Screen/LevelEnd` |
| 5 | `PlayerEndLevel` | `LevelCompleted`, `Screen/LevelEnd` |
| 6 | `PlayerLoseLife` | `PlayerDied/Fall` (end of; see the fall-timing note), end of `Screen/Death` |
| 7 | `PlayerEntrance` | `Screen/Transition` (Mario emerging from a pipe or dropping into the area) |
| 8 | `PlayerCtrlRoutine` | normal play, `Screen/Gameplay` |
| 9 | `PlayerChangeSize` | start of `PlayerState/Super` (the status byte changes on this frame) |
| 10 | `PlayerInjuryBlink` | `PlayerDamaged`; the form row ends and `PlayerState/HitRecovery` starts |
| 11 | `PlayerDeath` | `PlayerDied/Enemy`, start of `Screen/Death` |
| 12 | `PlayerFireFlower` | start of `PlayerState/Fire` |

Using the engine rather than counters matters because counters lag: `lives` only drops
once the death animation has finished, several seconds after the death itself.

### On-screen visibility

| Dataset | Predicate | Validation |
|---|---|---|
| mario | `Enemy_Flag` set **and** `EnemyOffscrBitsMasked == 0` | horizontally inside the visible band on 97.5–98.9% of frames when 0, 0.0–1.5% when non-zero; `enemy_y` inside 0–239 on 99.9% of accepted frames, so no separate vertical test is needed |
| mariostars | bit 0 of `sprite_onscreen_flag_*` | no per-sprite coordinates exist in this port, so the predicate is checked indirectly by cross-port agreement with the NES on the 21 shared levels |

Scenery is the one deliberate exception and uses slot occupancy on its own, meaning
"spawned" rather than "on screen": `FlagpoleVisible` / `CastleVisible` (scenery never clears
the enemy offscreen test — 0 of 479 frames in a sampled replay), and any repetition whose
`_variables.json` predates the visibility addresses.

### Screens

| Row | Meaning | Detection |
|---|---|---|
| `Screen/Gameplay` | The player controls the character in the level. | engine 8, 9, 10, 12 |
| `Screen/LevelIntro` | The level's title card. | engine 0 (NES) / `OperMode_Task` ≠ 3 (SNES) at the start of the repetition or directly after a death: the black "WORLD x-y / Mario × n" card, 86-193 frames |
| `Screen/Death` | The death sequence, no control. | engine 11 through 6, or from the fall (see below) to 6 |
| `Screen/LevelEnd` | The end-of-level sequence, no control. | engine 4 then 5: flagpole slide, walk into the castle, time bonus, 6-14 s |
| `Screen/Transition` | Between areas, no control. | engine 1, 2, 3, 7 and the 0 / task ≠ 3 stretch between them: pipe travel, vine climb, the exit from a bonus area, 24 frames of black |

Every boundary was checked on rendered emulator frames. The SNES title card needs
`OperMode_Task` ($0772), which the engine variable cannot see (it idles at 8 while the
card is up); it is read out of the shipped `reset` variable, a 4-byte little-endian BCD
read at $0771 whose second byte pair is that task (1 = card, 3 = game routines). The SNES
fades in and out around the card, so those boundaries are within ~30 frames (0.5 s).

### Timing a fall death

`PlayerLoseLife` does not run when the player drops into a pit — it runs about **4 s
later**, once the game has let the player fall out of the level and is ready to reset.
Recording the death there puts it seconds after anything the player saw, so `onset` is
walked back to the frame the player actually left the screen and `duration` runs from
there to the life loss. The old timing is still available as `onset + duration`.

| Dataset | How the fall is dated | Accuracy |
|---|---|---|
| mario | `Player_Y_HighPos` (`player_y_screen`) leaving 1 — it is 1 on 95.0% of play frames, 0 above the screen, >1 below it | exact; 69 of 69 sampled fall deaths have the crossing, at a lag of 244–257 frames |
| mariostars | the frame the level timer stops ticking — the game freezes gameplay the moment the player drops out — plus half a tick | validated by running the same proxy on the NES against the exact crossing: median error −12 frames, **100% within 24 frames (0.4 s)**; the half-tick correction removes that bias |

The SNES port exposes no player-Y address, which is why it needs the proxy. The `scroll_x_low`
freeze was also tested as a proxy and is worse (only 77% within 0.4 s, p10 −50 frames),
so the timer is used.

### Player

| Event | Description | Detection |
|---|---|---|
| `PlayerDamaged` | Hit, losing the current power-up state. | `player_state` / `player_action_state` transitions to **10** (`PlayerInjuryBlink`). |
| `PlayerDied/Enemy` | Killed by an enemy or other damaging object. | Engine transitions to **11** (`PlayerDeath`). |
| `PlayerDied/Fall` | Fell into a pit. | Engine transitions to **6** (`PlayerLoseLife`) with no **11** in the preceding 400 frames — a fall bypasses the death routine. `onset` is walked back to the frame the player left the screen (see below); `duration` runs to the life loss. |
| `PlayerDied/Timeout` | The level timer ran out. | Engine reaches **11** while `time` / `time_units` has been 0 for the preceding 120 frames. |
| `LifeGained` | Gained an extra life. | `lives` increases. |
| `PlayerState/Small`, `PlayerState/Super`, `PlayerState/Fire` | The form the player is in, one row per continuous stretch. Together they tile the frames on which the player is alive in the level. | Maximal runs of `player_status` == **0** / **1** / **2** over the alive frames (outside `Screen/Death` and `Screen/LevelIntro`). `PlayerStatus` is written on the very frame the item is collected (engine **9** / **12**) and on the hit frame (engine **10**), so the row starts and ends on those frames. A row is cut at a death and Small resumes once the title card has gone. |
| `PlayerState/Star` | Star invincibility, whole period. | Non-zero run of `star_timer` (`StarInvincibleTimer`, $079F / $07AF): 35 → 0 on the 21-frame interval clock, ~730 frames. |
| `PlayerState/HitRecovery` | Post-hit invulnerability: the ~3.7 s after a hit during which `InjurePlayer` ignores enemy contact and the player blinks. | Non-zero run of `injury_timer` (`InjuryTimer`, $079E / $07AE, **new**): 8 → 0 on the interval clock, paused during the shrink animation. |

> On the SNES, `player_status`, `injury_timer` and `star_timer` are new in this release
> ($7E0756, $7E07AE, $7E07AF). The shipped `player_powerup` ($0578) and `star_power_timer`
> ($0553) hold unrelated bytes (values like 82 and 107, constants rather than a countdown)
> and are no longer read; see `ram.SMAS_CANDIDATES` for how the real ones were found.
>
> `player_status` is a variable added in this release, reading `PlayerStatus` at `$0756`
> as a single byte. The pre-existing `powerstate` reads the same address as 4-byte BCD,
> which mixes in the neighbouring death flag and reports values like 10000. Use
> `player_status`.

### Items and blocks

| Event | Description | Detection |
|---|---|---|
| `ItemCollected/Coin` | Collected a coin. | `coins` / `player_coins` increases, or drops by ≥99 (the counter wraps at 100 and awards a life). |
| `ItemOnScreen/Powerup` | A mushroom, flower or star became visible. | An enemy slot holds object id **`0x2E`** (`PowerUpObject`) and is visible. |
| `BlockSmashed` | Destroyed a brick from below. | `score` increases by exactly **5** (NES, BCD in units of 10 points) or **50** (SNES, actual points) while the player is airborne (`jump_airborne` ∈ {1,2} on the NES), before the level ends. The end-of-level time bonus produces the same increment, so scoring stops at the level end. |

### Enemies

| Event | Description | Detection |
|---|---|---|
| `EnemyOnScreen/{type}` | An enemy became visible. | A visible track opens in an object slot. Type from `enemy_id_*` / `sprite_number_*` decoded through the SMB1 object table. `duration` spans the visible lifetime. |
| `EnemyDefeated/Stomp/{type}` | Defeated by jumping on it. | `Enemy_State` / `sprite_state_*` transitions into **4** from a non-kill state. |
| `EnemyDefeated/Projectile/{type}` | Defeated by a fireball or similar. | The same array transitions into **34**. |
| `EnemyDefeated/Shell/{type}` | Defeated by a moving shell. | The same array transitions into **132**. |
| `ProjectileOnScreen/{type}` | A Bowser flame is on screen. | A visible track whose object id is **`0x15`** (BowserFlame). Bullet Bills are **not** here — see below. |

The defeat is emitted at the **first** frame of the kill state, i.e. when the enemy is
hit — not when its corpse finishes falling. This matters because on a projectile kill the
game deliberately moves the dying enemy's bounding box off screen, so reading the end of
the animation would place the event after the enemy stopped being visible.

A defeat names both the method and the species, e.g. `EnemyDefeated/Stomp/Goomba`.

**Object ids that are not enemies** and are excluded from `Enemy_*`: moving platforms and
lifts (`0x24`–`0x2C`), items and scenery (`0x16`, `0x2E`, `0x2F`, `0x30`, `0x31`, `0x32`,
`0x35`, `0x36`), spawner/control objects (`0x17`, `0x18`) and the Bowser flame (`0x15`).

#### Bullet Bills are enemies, and live under two ids

A Bullet Bill can be stomped for points and kills the player on contact, so it is an
enemy rather than a projectile. It occupies **two** object ids depending on which spawner
made it — `0x08` from a frenzy, `0x33` from a cannon — and the disassembly names both
after the spawner rather than after the object. Both now decode to `BulletBill`.

`0x33` used to be classed as a spawner and discarded outright, which threw away most of
the Bullet Bills in both datasets: over 120 mario replays it accounts for **331** flying
runs against 90 for `0x08` (mariostars: 283 against 43). Runs of the two ids are
indistinguishable in motion — both travel at a median **1.5 px/frame**. On one sampled
session this took `BulletBill` from 25 tracks to 267.

The id is shared with the stationary cannon that fires them. On the NES, where per-slot X
is available, a track is kept only if it moves in X on at least half its frames; 90% of
visible tracks pass. The SNES port exposes no per-sprite X, so the test cannot run there
and roughly 10% of its `EnemyOnScreen/BulletBill` tracks are expected to be the cannon.

#### Piranha Plants count only while out of the pipe

A Piranha Plant holds its slot for the whole cycle — rising, waiting, retracting, then
sitting inside the pipe — and the offscreen bits describe only the horizontal edges, so
the slot reads as visible even while the plant is hidden and cannot touch the player.

Its screen Y traces the cycle exactly: over 60 mario replays the plant moves through 25
distinct Y values spanning **24 px**, resting at the maximum. Within each run of the slot
the resting position is that maximum, and the plant is out whenever it sits above it. A
run that never shows the full 24 px cannot identify its own resting position and is left
visible throughout rather than guessed at.

**34.2%** of what used to count as visible Piranha Plant time was the plant hidden in its
pipe. One long track per pipe becomes one event per emergence: on a sampled session, 141
tracks of median 3.06 s became 228 of median 1.72 s.

`Enemy_State` was checked first and is **0** for the entire cycle, so it cannot serve —
which is why the SNES port, exposing no per-sprite Y, keeps the old behaviour.

Note that **id `0x00` is Green Koopa**, a real enemy — a zero id does not mean an empty
slot. Slot occupancy is given by `Enemy_Flag`, not by the id.

### Environment and level

| Event | Description | Detection |
|---|---|---|
| `PipeEntered` | Entered a pipe. | Engine transitions to **2** (`SideExitPipeEntry`) or **3** (`VerticalPipeEntry`). |
| `FlagpoleVisible` | The end-of-level flagpole came on screen. | An object slot holds id **`0x30`** (`FlagpoleFlagObject`). Judged by slot occupancy alone, because scenery never clears the enemy offscreen test. |
| `CastleVisible` | The end-of-level star flag / castle came on screen. | The same, with id **`0x31`** (`StarFlagObject`). |
| `TimerWarningStarted` | The game began warning that time is short. | NES: bit **`0x40`** of `event_music_queue` (the game's own "time running out" music cue). SNES: the timer crossing 100 downward during normal play. |
| `LevelStarted` | A gameplay attempt began. | Frame 0 of the repetition. |
| `LevelCompleted` | The level was finished. | Engine transitions to **5** (`PlayerEndLevel`), falling back to **4** (`FlagpoleSlide`). Using `PlayerEndLevel` means this also fires on castle levels, which end at an axe rather than a flagpole. |
| `LevelExited/Warp` | The player left through a warp-zone pipe. | The `world` / `area` index changes **and** the level never ended. Only fires on w1-2 and w4-2, the two warp-zone levels. |

> **`CheckpointReached` is deliberately not emitted.** Its only candidate signal,
> `HalfwayPage` (`$075B`), is written when the player *dies* past the midpoint in order to
> place the respawn — not when the midpoint is crossed. In a sampled w1-1 replay it is
> non-zero only during the two death/respawn sequences.

### Controller actions

| Event | NES | SNES |
|---|---|---|
| `Action/Left`, `Action/Right`, `Action/Up`, `Action/Down` | D-pad | D-pad |
| `Action/Jump` | `A` | `B`, `A` |
| `Action/Run` | `B` | `Y`, `X` |
| `Action/Start` | `START` | `START` |
| `Action/Select` | `SELECT` | `SELECT` |
| `Action/Other` | — | `L`, `R` |

The SNES `L` and `R` buttons have no documented function in this game; the previous
pipeline dropped them entirely (`L` is pressed 30 times in a single sampled replay).

### Repetition outcomes

The label describes how the repetition *ended*, so when several lives are lost only the
final death is classified. The previous logic tested `jump_airborne == 3`, which is the
flagpole slide **and** the vine climb, so warps taken up a vine were labelled `cleared`;
71 mario and 59 mariostars repetitions changed label when this was corrected.

### Provenance

RAM addresses and value tables are taken from published sources and each was verified
against an independent signal before being used:

- **Super Mario Bros.** — [1wErt3r's SMBDIS.ASM](https://gist.github.com/1wErt3r/4048722)
- **Super Mario All-Stars** — [Data Crystal's partial RAM map](https://datacrystal.tcrf.net/wiki/Super_Mario_All-Stars_(SNES)/RAM_map),
  plus the empirical finding that its object ids match SMB1's verbatim

Cross-port agreement between the NES and SNES versions (V2): 15 of the 21 levels
containing enemies yield identical rosters on the two consoles.
