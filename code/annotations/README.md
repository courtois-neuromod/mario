# Mario Annotations Generator

This script generates BIDS-compatible annotated event files (`*_desc-annotated_events.tsv`) for the Super Mario Bros dataset. It reads pre-processed game variables and computes detailed annotations for all gameplay events including button presses, enemy kills, hits taken, item collection, and more.

## Prerequisites

- Python 3.8 or higher
- The Mario dataset with `.bk2` replay files
- **Replays must be processed first** using `code/replays/create_replays.py` to generate `*_variables.json` files
- ROM files in the `stimuli/` directory

## Installation

### 1. Create a Python virtual environment

From the root directory of the mario repository:

```bash
python -m venv env
```

### 2. Activate the environment

```bash
source env/bin/activate  # On Linux/Mac
# OR
env\Scripts\activate  # On Windows
```

### 3. Install dependencies

```bash
pip install -r code/annotations/requirements.txt
```

This will install:
- numpy
- pandas
- stable-retro

## Usage

### Basic Usage

From the root directory of the mario repository:

```bash
python code/annotations/generate_annotations.py --datapath .
```

This will:
- Scan all `*_events.tsv` files in the dataset
- Load corresponding replay variables from `gamelogs/*_variables.json`
- Generate `*_desc-annotated_events.tsv` files with detailed event annotations

### Options

```bash
# Specify a custom data path
python code/annotations/generate_annotations.py --datapath /path/to/mario

# Custom output path
python code/annotations/generate_annotations.py --datapath . --output_path /path/to/output

# Filter by subject
python code/annotations/generate_annotations.py --datapath . --subjects sub-01 sub-02

# Filter by session
python code/annotations/generate_annotations.py --datapath . --sessions ses-001 ses-002
```

## Generated Annotations

The script produces `*_desc-annotated_events.tsv` files with the following structure:

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
| phase | "discovery" or "practice" (see below) |

### Event Types

#### Repetition Events
- `gym-retro_game` - Base repetition events from the original events file

#### Button Press Events
Continuous events with onset and duration:
- `UP`, `DOWN`, `LEFT`, `RIGHT` - D-pad directions
- `A` - Jump button
- `B` - Run/fireball button
- `START` - Pause
- `SELECT` - Mode select

#### Enemy Kill Events
Instantaneous events (duration=0):
- `Kill/stomp` - Jumping on enemy
- `Kill/impact` - Shell or fireball hit
- `Kill/kick` - Kicked shell

#### Hit Events
Instantaneous events (duration=0):
- `Hit/powerup_lost` - Lost fire flower or super mushroom state
- `Hit/life_lost` - Death

#### Item Collection Events
Instantaneous events (duration=0):
- `Coin_collected` - Coin counter increases
- `Powerup_collected` - Super mushroom or fire flower collected
- `Brick_smashed` - Brick destroyed by jumping

### Phase Information

Each run is classified as:
- **discovery**: Single level repeated multiple times (practice/training)
- **practice**: Multiple different levels in sequence (testing)

## Dependencies

This script requires that replays have been processed first:

```bash
# First, process replays to generate variables
python code/replays/create_replays.py --datapath .

# Then run annotations
python code/annotations/generate_annotations.py --datapath .
```

## Troubleshooting

### "Variables file not found" errors
- Ensure you've run `code/replays/create_replays.py` first
- Check that `gamelogs/*_variables.json` files exist for each .bk2 file

### "No bk2 files available for this run"
- Normal if a run has no valid .bk2 files (all marked as "Missing file")

### ROM/stimuli errors
- Verify that `stimuli/SuperMarioBros-Nes/` contains the ROM files

### Already annotated files
- The script skips files that already have annotated versions
- To force regeneration, delete existing `*_desc-annotated_events.tsv` files
