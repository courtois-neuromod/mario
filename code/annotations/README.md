# Annotated event files - mario

`generate_annotations.py` turns the per-frame RAM dumps written by
`code/replays/generate_replays.py` (`gamelogs/*_variables.json`) into
BIDS event files at `sub-*/ses-*/func/*_desc-annotated_events.tsv`.

The event logic is shared by all four CNeuroMod videogame datasets and lives in
[`videogames_utils.events`](https://github.com/courtois-neuromod/videogames_utils);
this directory only holds the command-line front end. The machine-readable
vocabulary is published as `task-mario_events.json` at the dataset root.

## Usage

```bash
python code/annotations/generate_annotations.py -d . --overwrite --validate
```

## Columns

| Column | Description |
|---|---|
| `trial_type` | Event type, from the controlled vocabulary below. |
| `level` | Level of the repetition the event belongs to. |
| `onset` | Seconds from the start of the run. |
| `duration` | Seconds. 0 for point events. |
| `frame_start` | First emulator frame of the event, relative to its repetition. |
| `frame_stop` | Last emulator frame of the event, relative to its repetition. |
| `button` | Raw controller button behind an `Action/*` event. |
| `stim_file` | Path to the repetition's `.bk2` replay. |

Onsets are computed at the console's true frame rate (60.099827 Hz, read from the
emulator core), not the 60.0 Hz the pipeline previously assumed. That correction
shifts onsets by up to ~0.6 s in the longest repetitions.

## Event types

`{...}` is replaced at generation time with a decoded name.

| Event | Description |
|---|---|
| `Player_damaged` | The player is hit and loses the current power-up state (Mario games) or health (Shinobi). |
| `Player_died/Enemy` | The player dies after being hit by an enemy or another damaging object. |
| `Player_died/Fall` | The player falls into a pit and dies. `onset` is the frame `Player_Y_HighPos` (`player_y_screen`) leaves 1, i.e. the player drops below the screen; `duration` runs to the life loss ~4 s later. |
| `Player_died/Timeout` | The player dies because the level timer ran out. |
| `Life_gained` | The player collects or earns an extra life. |
| `Player_state/Super` | The player is Super (big) Mario, from the frame the mushroom is collected until hit, death or the end of the repetition. |
| `Player_state/Fire` | The player is Fire Mario (can throw fireballs). |
| `Player_state/Star` | Star invincibility is active. |
| `Player_state/Hit_recovery` | Post-hit recovery: the player has just been damaged and blinks. In the Mario games nothing can hurt the player until it ends; in Shinobi it is the game's post-hit counter. |
| `Item_on_screen/{item_type}` | A coin, mushroom, flower, star or extra life is visible on screen. `duration` spans the time it is visible. |
| `Item_collected/Coin` | The player collects a coin. |
| `Item_collected/Powerup` | The player collects a mushroom, flower, star or other power-up item. |
| `Block_smashed` | The player destroys a breakable brick block from below. |
| `Enemy_on_screen/{enemy_type}` | A specific enemy type is visible on screen. `duration` runs from the frame it becomes visible until it leaves the screen or is defeated; an enemy that leaves and returns produces two separate events. |
| `Enemy_attack/{enemy_type}` | An enemy begins an attack, such as firing a projectile or emerging from a pipe. |
| `Enemy_defeated/Stomp/{enemy_type}` | The player defeats an enemy by jumping on it. |
| `Enemy_defeated/Projectile/{enemy_type}` | The player defeats an enemy with a fireball or other projectile. |
| `Enemy_defeated/Shell/{enemy_type}` | The player defeats an enemy using a moving shell. |
| `Projectile_on_screen/{projectile_type}` | A fireball, Bullet Bill, hammer or other moving projectile is visible on screen. `duration` spans the time it is visible. |
| `Shell_started_moving` | A shell begins moving after being kicked or otherwise activated. |
| `Pipe_entered` | The player enters a pipe. |
| `Checkpoint_reached` | The player passes the level checkpoint that changes the restart position. |
| `Flagpole_visible` | The flagpole at the end of the level becomes visible on screen. |
| `Castle_visible` | The end-of-level castle becomes visible on screen. |
| `Timer_warning_started` | The game begins warning the player that little time remains. |
| `Level_started` | A new level or gameplay attempt begins. |
| `Level_restarted` | The level restarts after the player dies. |
| `Level_completed` | The player successfully finishes the level. |
| `Level_exited/Warp` | The player left the level through a warp-zone pipe rather than finishing it. Not part of Event-Types.pdf; retained from the previous vocabulary. |
| `Action/Left` | The player holds the left direction. |
| `Action/Right` | The player holds the right direction. |
| `Action/Up` | The player holds the up direction. |
| `Action/Down` | The player holds the down direction (duck / crouch). |
| `Action/Jump` | The player presses the jump button. |
| `Action/Run` | The player presses the run / throw button (Mario games). |
| `Action/Other` | The player presses a button with no documented function in this game (e.g. L/R on the SNES pad in Super Mario All-Stars). The raw button is in the `button` column. |
| `Action/Start` | The player presses START (pauses the game). |
| `Action/Select` | The player presses SELECT / MODE. |
| `gym-retro_game` | One repetition of gameplay (one .bk2 file). This is the container row that carries `stim_file`; all other events fall inside its window. |

## Renamed from the previous vocabulary

This release renames every event type. Old analyses filtering on the former
names need updating; the mapping is:

`Enemy_disappeared` was **dropped**: it was a point event on the last visible frame
of an `Enemy_on_screen` track that no defeat claimed, so it is exactly
`onset + duration` of that row (verified on 6620 of 6620 rows, matching on integer
frames). Read it as an `Enemy_on_screen` row with no `Enemy_defeated` at its end.

| Former | Now |
|---|---|
| `Brick_smashed` | `Block_smashed` |
| `Enemy_appeared/{enemy_type}` | `Enemy_on_screen/{enemy_type}` |
| `Enemy_disappeared/{enemy_type}` | *(dropped)* |
| `Item_appeared/{item_type}` | `Item_on_screen/{item_type}` |
| `Projectile_appeared/{projectile_type}` | `Projectile_on_screen/{projectile_type}` |
| `Coin_collected` | `Item_collected/Coin` |
| `DOWN` | `Action/Down` |
| `HealthLoss` | `Player_damaged` |
| `Hit/fall` | `Player_died/Fall` |
| `Hit/killed` | `Player_died/Enemy` |
| `Hit/life_lost` | `Player_died/Enemy` |
| `Hit/powerup_lost` | `Player_damaged` |
| `Hit/timeout` | `Player_died/Timeout` |
| `JUMP` | `Action/Jump` |
| `Kill/impact` | `Enemy_defeated/Projectile/{enemy_type}` |
| `Kill/kick` | `Enemy_defeated/Shell/{enemy_type}` |
| `Kill/stomp` | `Enemy_defeated/Stomp/{enemy_type}` |
| `LEFT` | `Action/Left` |
| `Level_complete` | `Level_completed` |
| `MODE` | `Action/Select` |
| `Powerup_collected` | `Item_collected/Powerup` |
| `RIGHT` | `Action/Right` |
| `RUN/THROW` | `Action/Run` |
| `SELECT` | `Action/Select` |
| `START` | `Action/Start` |
| `Star_activated` | `Player_state/Star` |
| `UP` | `Action/Up` |
| `Warp` | `Level_exited/Warp` |


The previous release's `Powerup_started/*` and `Powerup_expired/*` point events are
replaced by the durational `Player_state/*` rows: the onset of `Player_state/Super` is the
old `Powerup_started/Super`, the end of `Player_state/Star` is the old
`Powerup_expired/Star`, and so on. `Powerup_started/Small` (emitted on a hit) has no
successor: Small has no state row, and the hit is already `Player_damaged`.

### Accuracy notes

- `Player_state/*` rows are read straight from the RAM: `PlayerStatus` ($0756,
  `player_status`) for the form, which the game writes on the very frame a mushroom or
  flower is collected or a hit lands; `StarInvincibleTimer` ($079F, `star_timer`) for
  `Star`; and `InjuryTimer` ($079E, `injury_timer`, **new in this release**) for
  `Hit_recovery`, the ~3.7 s after a hit during which enemy contact is ignored. A row is
  cut at a death that falls inside it, since the game only resets the status on the
  restart. Validation recounts every row from the same series by a different route.
- Enemy visibility uses the game's own `EnemyOffscrBitsMasked` ($03D8). Validated against
  independently computed screen-relative positions: when it is zero the enemy is inside
  the visible band on 97.5-98.9% of frames, when non-zero on 0.0-1.5%.
- Enemy types come from `Enemy_ID` ($0016) decoded through the object table in
  1wErt3r's SMB disassembly. Cross-checked against mariostars: 5 of 7 levels played on
  both consoles yield identical enemy rosters.
- `Checkpoint_reached` is **not** emitted. Its only candidate signal, `HalfwayPage`
  ($075B), is written when the player *dies* past the level midpoint in order to place
  the respawn, not when the midpoint is crossed.
- `Level_completed` uses the engine's `PlayerEndLevel` routine, so it also fires on
  castle levels where there is no flagpole and the old `jump_airborne == 3` test could
  never trigger.
- `Level_exited/Warp` is detected from the world/area index changing, not from the
  summary `Outcome`: the shipped outcome logic tests `jump_airborne == 3`, which is the
  flagpole slide *and* the vine climb, so a W4-2 warp taken up the vine is mislabelled
  `cleared` in `_summary.json`.

## Validation

```bash
python -m videogames_utils.events.validate_cli check . mario
python -m videogames_utils.events.validate_cli cross-port ../mario ../mariostars
```

`check` runs two layers: the schema and controlled-vocabulary checks (V0), and
invariants recomputed straight from `_variables.json` by a different route than
the generator used (V1) -- coin counts against the coin counter, deaths against
the lives counter, level completion against the summary outcome, enemy track
bookkeeping, and frame-range bounds.

A human video review measures precision and recall per event type:

```python
from videogames_utils.events import review
review.build_review_set('.', 'mario', out_dir='/tmp/review', per_type=50)
# rate the clips in /tmp/review/review.html, then:
review.score_reviews('/tmp/review/ratings.json', '/tmp/review/manifest.json')
```
