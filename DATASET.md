# Super Mario Bros Dataset Overview

This repository is your entry point for working with the Super Mario Bros dataset from the [Courtois NeuroMod project](https://www.cneuromod.ca/).

## Dataset Overview

The dataset is composed of several repositories:

- [`mario`](https://github.com/courtois-neuromod/mario): The main repository containing the raw data as well as behavioral files
- [`mario.fmriprep`](https://github.com/courtois-neuromod/mario.fmriprep): Contains the outputs of fMRIPrep, this is where you will find preprocessed BOLD data
- [`mario.timeseries`](https://github.com/courtois-neuromod/mario.timeseries): Parcellated BOLD timeseries, computed from `mario.fmriprep`
- [`mario.physprep`](https://github.com/courtois-neuromod/mario.physprep): Preprocessed physiological timeseries
- [`mario.stimuli`](https://github.com/courtois-neuromod/mario.stimuli) (requires AWS access provided by the CNeuromod team): Contains the game ROM, save states used to initialize the game, and data.json that maps RAM addresses to interpretable variables. This repo (installed as a submodule of the present repo) is required to process `.bk2` files, but optional for most usecases

Additionally, several repositories extend the present dataset by providing tools and analyses that you can use to leverage your own:

- [`mario.tutorials`](https://github.com/courtois-neuromod/mario.tutorials): Tutorials for using the mario dataset to perform GLM analysis and brain encoding experiments
- [`mario.scenes`](https://github.com/courtois-neuromod/mario.scenes): Level-design analysis of SMB used to segment gameplay into analyzable units
- [`mario.fmri_analysis`](https://github.com/courtois-neuromod/mario.fmri_analysis): GLM-based analysis of game events present in the `*desc-annotated_events.tsv` files
- [`videogames_utils`](https://github.com/courtois-neuromod/videogames_utils): A set of utilitary functions to handle replay files and a GUI for QC purposes


The `mario` repository includes:

- **Gameplay recordings**: `.bk2` replay files capturing frame-per-frame gameplay
- **Event files**: BIDS-formatted timing information for each gameplay session
- **Game variables**: Extracted frame-by-frame game state (player position, score, enemies, etc.)
- **Videos**: Replay videos with audio
- **Low-level features**: Low-level features precomputed from the video (luminance, optical flow, audio envelope)
- **Annotated events**: Detailed event annotations (button presses, kills, item collection, etc.)

### Installation instructions

```bash
# Install datalad and git-annex
pip install datalad datalad-installer
datalad-installer git-annex

# Clone the dataset
datalad install git@github.com:courtois-neuromod/mario
cd mario

# Download all files (or use wildcards for specific files)
datalad get .
# e.g., datalad get */*/*/*.bk2
```

### General Information

- **Game**: Super Mario Bros (Nintendo Entertainment System, 1985), World/US version
- **Levels naming**: `w{world}l{level}` (e.g., w1l1, w8l4)
- **Frame rate**: 60 Hz (60 frames per second)
- **Files organization convention**: To differentiate the different hierchachical levels at which the data is organized we use the following convention: 
    - *session*: A scanning session, during which several runs have been acquired.
    - *run*: A continuous recording of fMRI data, containing several repetitions.
    - *repetition*: A singular attempt at clearing a level. Each repetition is associated with a `.bk2` file.
- **Synchronization**: The crucial link between the game and the brain is the `*desc-annotated_events.tsv` file. The `onset` column in this file corresponds to the time (in seconds) from the start of the fMRI run.


### Experimental Design

Participants played Super Mario Bros in a Siemens 3T MRI scanner, using the [CNeuromod Videogame Controller](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0290158) to play the game emulated via the [CNeuromod task codebase](https://github.com/courtois-neuromod/task_stimuli).

### Levels selection 

We selected 22 levels from the original game, excluding Waterworld and Bowser Castle levels:

- World 1: w1l1, w1l2, w1l3
- World 2: w2l1, w2l3
- World 3: w3l1, w3l2, w3l3
- World 4: w4l1, w4l2, w4l3
- World 5: w5l1, w5l2, w5l3
- World 6: w6l1, w6l2, w6l3
- World 7: w7l1, w7l3
- World 8: w8l1, w8l2, w8l3

The levels were presented following a two-phase logic in order to ensure 1) that players are familiar with the game and 2) that we have enough data to perform robust statistical analyses. Each presentation of a level is named a *repetition*, and consists of an attempt of three lives to complete the level.

- **Discovery phase**: Levels are presented in order. In a given run, a single level is repeated until the player is able to complete it at least once. If the level have been completed, the next run will present the next level in the sequence 
- **Practice phase**: Multiple different levels are presented in a pseudo-random order in a single run. After a level have been played, it will not be presented again until all the remaining levels have been presented.


## Notable files and folders
This repository contains the raw MRI acquisition as well as a set of pre-computed files describing the stimulation (game replays and events files). In most cases, you will want these files in combination with the preprocessed MRI provided in `mario.fmriprep`, `mario.timeseries` or `mario.physprep`. 

```
mario/
├── CHANGES                                  # Version history
├── DATASET.md                               # This file
├── README                                   # Brief overview
├── dataset_description.json                 # BIDS dataset metadata
├── participants.json                        # Participant metadata schema
├── participants.tsv                         # Participant information
├── physio.json                              # Physiological data metadata
├── scans.json                               # Scan metadata schema
├── task-mario_bold.json                     # BOLD task parameters
├── stimuli/                                 # Game ROM and configuration files (mario.stimuli submodule)
├── code/                                    # Processing scripts for provenance tracking
└── sub-XX/                                  # Subject directories
    └── ses-XXX/                             # Session directories
        ├── anat/                            # Anatomical data (localizers/scouts)
        │   ├── *_localizer*.nii.gz          # Localizer images
        │   ├── *_localizer*.json            # Localizer metadata
        │   ├── *_scout.nii.gz               # Scout images
        │   └── *_scout.json                 # Scout metadata
        ├── fmap/                            # Fieldmaps for distortion correction
        │   ├── *_acq-bold_dir-AP_epi.nii.gz # AP phase-encode EPI
        │   ├── *_acq-bold_dir-AP_epi.json   # AP EPI metadata
        │   ├── *_acq-sbref_dir-*_epi.nii.gz # Single-band reference images
        │   └── *_acq-sbref_dir-*_epi.json   # SBRef metadata
        ├── func/                            # Functional MRI data
        │   ├── *_part-mag_bold.nii.gz       # BOLD magnitude images
        │   ├── *_part-mag_bold.json         # BOLD magnitude metadata
        │   ├── *_part-phase_bold.nii.gz     # BOLD phase images
        │   ├── *_part-phase_bold.json       # BOLD phase metadata
        │   ├── *_part-mag_sbref.nii.gz      # Single-band reference (magnitude)
        │   ├── *_part-phase_sbref.nii.gz    # Single-band reference (phase)
        │   ├── *_physio.tsv.gz              # Physiological recordings
        │   ├── *_physio.json                # Physio metadata
        │   ├── *_events.tsv                 # Replay event timings
        │   └── *_desc-annotated_events.tsv  # Replay timings + aligned game events
        └── gamelogs/                        # Gameplay data (generated from .bk2 files)
            ├── *.bk2                        # Replay files
            ├── *_summary.json               # Summary data
            ├── *_recording.mp4              # Video replays
            ├── *_variables.json             # Game variables
            └── *_lowlevel.npy               # Low-level features
```

## Behavioral files content

### Summary files

Each replay includes high-level information:
- Duration, World, Level
- Score gained, distance traveled, average speed
- Lives lost, hits taken, enemies killed
- Powerups collected, bricks destroyed, coins gained
- Level cleared status

### Game Variables

The dataset includes detailed game state variables at 60 Hz:
- **Player position**: X_player, Y_player, xscrollHi/Lo
- **Player state**: lives, powerstate, player_state
- **Enemy tracking**: enemy_kill30-35 (6 enemy slots)
- **Score tracking**: score, coins
- **Physics state**: jump_airborne
- **Button inputs**: UP, DOWN, LEFT, RIGHT, A, B, START, SELECT


### Enriched (annotated) events files

These TSV files (`*_desc-annotated_events.tsv`) contain game events aligned to fMRI
timing. They are generated from the per-frame RAM dumps in `gamelogs/*_variables.json` by
`code/annotations/generate_annotations.py`, a thin front end over the shared
[`videogames_utils.events`](https://github.com/courtois-neuromod/videogames_utils)
package. Each row is either a **repetition** (`gym-retro_game`, which carries `stim_file`)
or a **game event** inside one.

Three documents describe them, from short to exhaustive:

- **`task-mario_events.json`** at the dataset root: the BIDS sidecar, with every column
  and every `trial_type` this game may emit.
- **`code/annotations/README.md`**: generated from the same vocabulary, with the number
  of rows each event has in this dataset, the entries that are defined but never produced
  and why, and the accuracy notes for this game.
- [`docs/EVENT_REFERENCE.md`](https://github.com/courtois-neuromod/videogames_utils/blob/main/docs/EVENT_REFERENCE.md)
  in `videogames_utils`: the cross-game reference, with the RAM address, value and
  validation figure behind every event.

**Columns:** `trial_type`, `level`, `onset`, `duration`, `frame_start`, `frame_stop`,
`button`, `stim_file`. Per-repetition metadata (`phase`, `IndexInRun`, `IndexGlobal`,
`IndexLevel`, `Outcome`) is not repeated on event rows; it lives in the repetition's
`gamelogs/*_summary.json`, keyed by the `stim_file` of the container row.

Onsets are computed at the console's true frame rate (60.099827 Hz, read from the
emulator core) rather than the 60.0 Hz previously assumed.

**Event types** are drawn from a controlled vocabulary shared by all four CNeuroMod
videogame datasets, grouped as: player events (`Player_damaged`, `Player_died/*`,
`Life_gained`), player states (`Player_state/*`: one durational row per stretch of
Small, Super or Fire, which together cover every frame the player is alive, plus Star and
post-hit recovery overlays), screens (`Screen/*`: one durational row per stretch of
gameplay, title card, death sequence, end-of-level sequence or transition, which together
partition every repetition), items and blocks (`Item_on_screen/*`, `Item_collected/*`,
`Block_smashed`), enemies (`Enemy_on_screen/*`, `Enemy_defeated/{Stomp,Projectile,Shell}/*`),
environment (`Pipe_entered`, `Flagpole_visible`, `Castle_visible`,
`Timer_warning_started`), level events (`Level_started`, `Level_completed`,
`Level_exited/Warp`) and controller actions (`Action/*`, with the raw button in the
`button` column).

> **Note on a vocabulary change.** Every `trial_type` was renamed relative to the first
> release of these files. The former names (`Kill/stomp`, `Hit/life_lost`,
> `Coin_collected`, `Powerup_started/*`, `JUMP`, ...) no longer appear. The full
> old-to-new mapping is in `code/annotations/README.md`.

## Citation

If you use this dataset in your research, please cite:

```
[Citation information will be added]
```
