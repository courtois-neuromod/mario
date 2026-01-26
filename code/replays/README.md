# Mario Replay Processing

Processes `.bk2` replay files to generate video, metadata, game variables, and low-level features.

## Prerequisites & Installation

1.  **Environment**: Python 3.8+, Mario dataset (with `.bk2` replays), and ROMs in `stimuli/`.
2.  **Setup**:
    ```bash
    python -m venv env
    source env/bin/activate
    pip install -r code/replays/requirements.txt
    ```

## Usage

```bash
python code/replays/generate_replays.py
```

### Arguments
-   `--datapath`: Root directory of the dataset.
-   `--output`: Output directory.
-   `--skip_videos`, `--skip_variables`, `--skip_lowlevel`: Skip specific outputs.
-   `--n_jobs`: Number of parallel jobs (default: all cores).
-   `--subjects`, `--sessions`: Filter processing.
-   `--stimuli`: Custom path for ROMs.
-   `--verbose`: Enable detailed logging.

## Generated Files

For each replay (e.g., `sub-{subject}_ses-{session}_task-mario_run-{run}_rep-{replay}.bk2`):
1.  `*_recording.mp4`: Video recording.
2.  `*_variables.json`: Frame-by-frame RAM variables.
3.  `*_lowlevel.npy`: Luminance, optical flow, and audio features.
4.  `*_summary.json`: Summary metadata (BIDS sidecar).

## Summary Variables (in sidecar JSON)

All variables rely on RAM addresses defined in `stimuli/SuperMarioBros-Nes/data.json`.

| Variable | Source / Logic |
| :--- | :--- |
| **Duration** | Total replay duration in seconds. |
| **Outcome** | `cleared` (flag grabbed via jump_airborne == 3), `failed/timeout` (timer=0), `failed/fall` (off-screen or lives=-1), `failed/killed` (player_state 6 or 11). |
| **X_traveled** | Max distance reached from start. |
| **Enemies_killed** | Count of enemies killed (stomp, impact, kick). |
| **Hits_taken** | Count of powerup losses + life losses. |
| **Bricks_smashed** | Count of `score` increments of 5 while airborne. |
| **Coins** | Coin count changes. |
| **Powerups_collected** | Count of powerup collections (player_state transitions). |
| **Phase** | `discovery` (level repeats) or `practice` (sequential progression). |
