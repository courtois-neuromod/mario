# Mario Replay Processing

This script processes `.bk2` replay files from the Super Mario Bros dataset and generates various outputs including videos, metadata, game variables, and low-level psychophysical features.

## Prerequisites

- Python 3.8 or higher
- The Mario dataset with `.bk2` replay files
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
pip install -r code/replays/requirements.txt
```

This will install all required packages including:
- numpy, pandas
- retro, stable-retro (for replay processing)
- joblib, tqdm (for parallel processing)
- videogames_utils (from local ../../videogames_utils - includes moviepy for video generation)

**Note**: The videogames_utils package is installed from the local repository at `../../videogames_utils` relative to the mario repo. Make sure this directory exists and is up to date.

## Usage

### Basic Usage

From the root directory of the mario repository:

```bash
python code/replays/generate_replays.py --datapath . --output .
```

This will:
- Scan all `*_events.tsv` files in the dataset
- Process all `.bk2` replay files referenced in those events
- Generate all output files by default in `sub-XX/ses-XXX/gamelogs/` directories

### Output Files

For each `.bk2` replay file, the following files are generated (all BIDS-compliant naming):

1. **`*_recording.mp4`** - Video playback of the replay with audio
2. **`.json`** - Metadata sidecar with Mario-specific statistics:
   - Duration, World, Level
   - Score gained, distance traveled, average speed
   - Lives lost, hits taken, enemies killed
   - Powerups collected, bricks destroyed, coins gained
   - Level cleared status
3. **`*_variables.json`** - Frame-by-frame game variables:
   - Player position (X_player, Y_player, xscrollHi/Lo)
   - Player state (powerstate, player_state, lives)
   - Enemy kill slots (enemy_kill30-35)
   - Score, coins, jump_airborne
   - Button presses (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT)
4. **`*_lowlevel.npy`** - Low-level psychophysical features:
   - Luminance
   - Optical flow
   - Audio envelope per frame

### Skipping Specific Outputs

If you want to skip certain outputs (e.g., to save time/space), use the `--skip_*` flags:

```bash
# Skip video generation (fastest, saves most space)
python code/replays/generate_replays.py --datapath . --output . --skip_videos

# Skip multiple outputs
python code/replays/generate_replays.py --datapath . --output . --skip_videos --skip_variables

# Only generate JSON metadata
python code/replays/generate_replays.py --datapath . --output . --skip_videos --skip_variables --skip_lowlevel
```

Available skip flags:
- `--skip_videos` - Skip video generation
- `--skip_variables` - Skip game variables extraction
- `--skip_lowlevel` - Skip low-level features computation

### Mario-Specific Features

#### Level Naming Convention

Mario uses world-level naming: `level-w{world}l{level}`
- Examples: `w1l1`, `w2l3`, `w4l2`
- World 1-8, Levels 1-4

#### Repetition Naming

Mario uses 3-digit repetition indices: `rep-001`, `rep-002`, etc.

#### Discovery vs Practice Phases

The script automatically detects:
- **Discovery**: Single level repeated multiple times
- **Practice**: Multiple different levels in sequence

### Advanced Options

```bash
# Use parallel processing with multiple jobs (default is all cores)
python code/replays/generate_replays.py --datapath . --output . --n_jobs 4

# Use all available CPU cores (default)
python code/replays/generate_replays.py --datapath . --output . --n_jobs -1

# Use single-threaded processing
python code/replays/generate_replays.py --datapath . --output . --n_jobs 1

# Verbose output
python code/replays/generate_replays.py --datapath . --output . --verbose

# Custom stimuli path (if ROMs are in a different location)
python code/replays/generate_replays.py --datapath . --output . --stimuli /path/to/stimuli

# Filter by subject
python code/replays/generate_replays.py --datapath . --output . --subjects sub-01 sub-02

# Filter by session
python code/replays/generate_replays.py --datapath . --output . --sessions ses-001 ses-002

# Filter by both
python code/replays/generate_replays.py --datapath . --output . --subjects sub-01 --sessions ses-001
```

## How It Works

1. **Discovery**: The script walks through the dataset directory and finds all `*_events.tsv` files
2. **Extraction**: For each events file, it extracts the list of `.bk2` replay files
3. **Ordering**: Replays are sorted and assigned:
   - Global index (across all replays for a subject)
   - Level-specific index (for each world-level combination)
4. **Phase Detection**: Determines if each run is discovery (single level) or practice (multiple levels)
5. **Smart Processing**: For each replay, the script checks which outputs already exist and only regenerates missing files
6. **Processing**: Replays are processed in parallel by default (use `--n_jobs 1` for sequential processing)

## Mario-Specific Event Detection

The script computes high-level statistics for Mario gameplay:

### Enemy Kills
- Tracked via `enemy_kill30-35` variables (6 enemy slots)
- Values: 4 (stomp), 34 (impact), 132 (kick)
- Special handling for slot 5 (powerup enemies)

### Brick Destruction
- Detected by score increase of 5 points while airborne (`jump_airborne == 1`)

### Hits Taken
- **Powerup lost**: `powerstate` decreases by >10000
- **Life lost**: `lives` counter decreases

### Powerup Collection
- Detected via `player_state` in [9, 12, 13] (powerup animation states)

### Coin Collection
- Tracked via `coins` counter increases

## File Structure

```
mario/
├── sub-01/
│   ├── ses-001/
│   │   ├── func/
│   │   │   └── sub-01_ses-001_task-mario_run-01_events.tsv
│   │   └── gamelogs/
│   │       ├── sub-01_ses-001_task-mario_run-01_level-w1l1_rep-001.bk2
│   │       ├── sub-01_ses-001_task-mario_run-01_level-w1l1_rep-001.json
│   │       ├── sub-01_ses-001_task-mario_run-01_level-w1l1_rep-001_recording.mp4
│   │       ├── sub-01_ses-001_task-mario_run-01_level-w1l1_rep-001_variables.json
│   │       └── sub-01_ses-001_task-mario_run-01_level-w1l1_rep-001_lowlevel.npy
│   └── ...
├── stimuli/
│   └── SuperMarioBros-Nes/  # or SuperMarioBrosSimple-Nes
├── code/
│   └── replays/
│       ├── generate_replays.py
│       ├── requirements.txt
│       └── README.md
└── env/  # Created by you
```

## Troubleshooting

### "File not found" errors for .bk2 files
- Ensure the `.bk2` files exist in the paths specified in the `*_events.tsv` files
- The paths in events.tsv should be relative to the dataset root

### ROM/stimuli errors
- Make sure the `stimuli/` directory exists in the dataset root
- Verify that `stimuli/SuperMarioBros-Nes/` contains the ROM and game data files

### Memory issues
- Use fewer parallel jobs: `--n_jobs 2`
- Skip videos: `--skip_videos`
- Process one subject at a time: `--subjects sub-01`

### Already processed files
- The script automatically detects existing outputs and skips them
- To force regeneration, delete the existing output files

### Position reset issues
- The script automatically fixes X position resets where the player position jumps back to 0
- This is handled internally via position continuity correction

## Performance Tips

- **Fastest**: `--skip_videos --skip_lowlevel` (only JSON + variables)
- **Balanced**: `--skip_videos`
- **Full processing**: No skip flags (default - generates everything)

Processing time per replay (approximate):
- JSON only: ~1-2 seconds
- With video: ~10-30 seconds
- With all outputs: ~30-60 seconds

For parallel processing, expect roughly linear speedup up to the number of physical CPU cores.

## Questions or Issues?

If you encounter any problems or have questions about the script, please check:
1. That all dependencies are installed correctly
2. That the virtual environment is activated
3. That you're running with correct `--datapath` and `--output` arguments
4. The verbose output for detailed error messages: `--verbose`
