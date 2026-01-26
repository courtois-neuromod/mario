# Mario Annotations Generator

Generates BIDS-compatible `*_desc-annotated_events.tsv` files from pre-processed game variables.

## Prerequisites & Installation

1.  **Environment**: Python 3.8+, Mario dataset (with `.bk2` replays).
2.  **Replays must be processed first** using `code/replays/generate_replays.py` to generate `*_variables.json` files.
3.  **Setup**:
    ```bash
    python -m venv env
    source env/bin/activate
    pip install -r code/annotations/requirements.txt
    ```

## Usage

```bash
python code/annotations/generate_annotations.py
```

### Arguments
-   `--datapath`: Root directory of the dataset.
-   `--output_path`: Custom output path.
-   `--subjects`, `--sessions`: Filter processing.

## Generated Annotations

The script produces BIDS-compatible `*_desc-annotated_events.tsv` files with the following structure:

### Column Order

| Column | Description |
|--------|-------------|
| trial_type | Type of event (see below) |
| rep_index | Repetition index within the run (integer) |
| level | Level identifier (e.g., "w1l1", "w2l3") |
| onset | Time in seconds from the start of the run (3 decimal places) |
| duration | Duration of the event in seconds (3 decimal places) |
| frame_start | Frame index where event starts (integer) |
| frame_stop | Frame index where event ends (integer) |
| phase | "discovery" or "practice" |

### Event Types

#### Repetition Events
- `gym-retro_game` - Base repetition events from the original events file

#### Button Press Events
Continuous events with onset and duration:
- `UP`, `DOWN`, `LEFT`, `RIGHT` - D-pad directions
- `JUMP` - Jump button
- `RUN/THROW` - Run/fireball button
- `START`, `SELECT`

#### Enemy Kill Events
Instantaneous events (duration=0):
- `Kill/stomp` - Jumping on enemy
- `Kill/impact` - Shell or fireball hit
- `Kill/kick` - Kicked shell

#### Hit Events
Instantaneous events (duration=0):
- `Hit/powerup_lost` - Lost powerup state (detected via any decrement in `powerstate`)
- `Hit/life_lost` - Death by enemy
- `Hit/fall` - Death by falling in pit

#### Item Collection Events
Instantaneous events (duration=0):
- `Coin_collected` - Coin counter increases
- `Powerup_collected` - Super mushroom or fire flower collected
- `Brick_smashed` - Brick destroyed (detected via score increment of 5 while airborne)

#### Level Completion Events
Instantaneous events (duration=0):
- `Level_complete` - Flag grabbed (detected via jump_airborne == 3)

### Phase Information

Each run was performed in one of these two phases:
- **discovery**: Single level repeated multiple times (practice/training)
- **practice**: Multiple different levels in sequence (testing)
