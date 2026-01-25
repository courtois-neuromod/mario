#!/usr/bin/env python
"""
Generate annotated event files for the Mario dataset from replay variables.

This script reads game variables from replay processing and generates detailed
BIDS-compatible event files containing:
  - Button press events (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT)
  - Kill events (stomp, impact, kick)
  - Hit events (powerup lost, life lost)
  - Brick smashing events
  - Coin collection events
  - Powerup collection events

Usage:
    python generate_annotations.py
    
    Or with explicit paths:
    python generate_annotations.py --datapath /path/to/mario

Note: Requires replay files (_variables.json) in gamelogs/ folders.
      Run create_replays.py first if they don't exist.
"""

import argparse
import os
import os.path as op
import pandas as pd
import numpy as np
import json


def create_runevents(runvars, run_id, events_dataframe, FS=60):
    """Create a BIDS compatible events dataframe from game variables and start/duration info of repetitions

    Parameters
    ----------
    runvars : list
        A list of repvars dicts, corresponding to the different repetitions of a run. Each repvar must have it's own duration and onset.
    events_dataframe : pandas.DataFrame
        A BIDS-formatted DataFrame specifying the onset and duration of each repetition.
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format.
    """
    all_df = [events_dataframe]
    for idx, repvars in enumerate(runvars):
        n_frames_total = len(repvars["START"])
        repvars["rep_onset"] = [events_dataframe["onset"][idx]]
        repvars["rep_duration"] = n_frames_total / FS
        rep_index = events_dataframe['rep_index'].iloc[idx]

        if len(repvars.keys()) > 0:  # Check if repetition logs are available
            # Actions
            ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "A", "B", "START", "SELECT"]
            for act in ACTIONS:
                temp_df = generate_key_events(repvars, act, FS=FS)
                temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
                temp_df["rep_index"] = rep_index
                all_df.append(temp_df)

            # Kills
            temp_df = generate_kill_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            temp_df["rep_index"] = rep_index
            all_df.append(temp_df)

            # Hits taken
            temp_df = generate_hits_taken_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            temp_df["rep_index"] = rep_index
            all_df.append(temp_df)

            # Bricks smashed
            temp_df = generate_bricks_smashed_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            temp_df["rep_index"] = rep_index
            all_df.append(temp_df)

            # Coins collected
            temp_df = generate_coin_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            temp_df["rep_index"] = rep_index
            all_df.append(temp_df)

            # Powerups
            temp_df = generate_powerup_events(repvars, FS=FS)
            temp_df["onset"] = temp_df["onset"] + repvars["rep_onset"]
            temp_df["rep_index"] = rep_index
            all_df.append(temp_df)

    try:
        events_df = pd.concat(all_df).sort_values(by="onset").reset_index(drop=True)
        
        # Round onset and duration to 3 decimal places
        events_df['onset'] = events_df['onset'].round(3)
        events_df['duration'] = events_df['duration'].round(3)
        
        # Ensure integer types for frame columns and rep_index
        for col in ['frame_start', 'frame_stop', 'rep_index']:
            if col in events_df.columns:
                events_df[col] = events_df[col].astype('Int64')  # nullable integer
        
        # Reorder columns: trial_type, rep_index, level, onset, duration, frame_start, frame_stop, phase
        cols = events_df.columns.tolist()
        priority_cols = ['trial_type', 'rep_index', 'level', 'onset', 'duration', 'frame_start', 'frame_stop', 'phase']
        priority_cols = [c for c in priority_cols if c in cols]  # only include existing columns
        other_cols = [c for c in cols if c not in priority_cols]
        events_df = events_df[priority_cols + other_cols]
        
    except ValueError:
        print("No bk2 files available for this run. Returning empty df.")
        events_df = pd.DataFrame()
    return events_df


def generate_key_events(repvars, key, FS=60):
    """Create a BIDS compatible events dataframe containing key (actions) events

    Parameters
    ----------
    repvars : list
        A dict containing all the variables of a single repetition
    key : string
        Name of the action variable to process
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format containing the
        corresponding action events.
    """

    var = np.multiply(repvars[key], 1)
    # always keep the first and last value as 0 so diff will register the state transition
    var[0] = 0
    var[-1] = 0

    var_bin = [int(val) for val in var]
    diffs = list(np.diff(var_bin, n=1))
    presses = [round(i / FS, 3) for i, x in enumerate(diffs) if x == 1]
    releases = [round(i / FS, 3) for i, x in enumerate(diffs) if x == -1]
    frame_start = [i for i, x in enumerate(diffs) if x == 1]
    frame_stop = [i for i, x in enumerate(diffs) if x == -1]
    onset = presses
    level = [repvars["level"] for x in onset]
    duration = [round(releases[i] - presses[i], 3) for i in range(len(presses))]
    duration = [round(releases[i] - presses[i], 3) for i in range(len(presses))]
    
    event_name = key
    if key == "A":
        event_name = "JUMP"
    elif key == "B":
        event_name = "RUN/THROW"
        
    trial_type = ["{}".format(event_name) for i in range(len(presses))]
    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_kill_events(repvars, FS=60):
    """Create a BIDS compatible events dataframe containing kill events.

    Mario has three types of kills based on enemy_kill3X variable values:
    - 4: stomp (jumping on enemy)
    - 34: impact (shell or fireball)
    - 132: kick (kicked shell)

    Parameters
    ----------
    repvars : list
        A dict containing all the variables of a single repetition.
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format containing the
        kill events.
    """
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    killvals_dict = {4: "stomp", 34: "impact", 132: "kick"}

    n_frames_total = len(repvars["START"])
    for frame_idx in range(n_frames_total - 1):
        for ii in range(6):
            curr_val = repvars[f"enemy_kill3{ii}"][frame_idx]
            next_val = repvars[f"enemy_kill3{ii}"][frame_idx + 1]
            if curr_val in [4, 34, 132] and curr_val != next_val:
                killstring = f"Kill/{killvals_dict[curr_val]}"
                if ii == 5:
                    if repvars["powerup_yes_no"] == 0:
                        onset.append(frame_idx / FS)
                        duration.append(0)
                        trial_type.append(killstring)
                        level.append(repvars["level"])
                        frame_start.append(frame_idx)
                        frame_stop.append(frame_idx)
                else:
                    onset.append(frame_idx / FS)
                    duration.append(0)
                    trial_type.append(killstring)
                    level.append(repvars["level"])
                    frame_start.append(frame_idx)
                    frame_stop.append(frame_idx)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_hits_taken_events(repvars, FS=60):
    """Generate events for when Mario takes damage or loses a life.

    Two types of hits:
    - Powerup lost: powerstate decreases by more than 10000
    - Life lost: lives counter decreases

    Parameters
    ----------
    repvars : dict
        Dictionary containing all the variables of a single repetition
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df : pandas.DataFrame
        Events DataFrame in BIDS-compatible format
    """
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    # Powerup lost
    diff_state = list(np.diff(repvars["powerstate"]))
    for idx_val, val in enumerate(diff_state):
        if val < -10000:
            onset.append(idx_val / FS)
            duration.append(0)
            trial_type.append("Hit/powerup_lost")
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    # Lives lost
    diff_lives = list(np.diff(repvars["lives"]))
    for idx_val, val in enumerate(diff_lives):
        if val < 0:
            # Check for fall (gap death) based on vertical velocity
            is_fall = False
            if "player_y_pos" in repvars:
                # Calculate velocity around the event
                # Look at 10 frames before death
                check_start = max(0, idx_val - 10)
                check_end = idx_val
                
                if check_end > check_start:
                    y_pos_segment = repvars["player_y_pos"][check_start:check_end+1]
                    # Calculate frame-to-frame velocity
                    velocities = [y_pos_segment[i+1] - y_pos_segment[i] for i in range(len(y_pos_segment)-1)]
                    
                    # Typical fall velocity in SMB1 is around 4-5 pixels per frame downward (positive Y)
                    # We look for consistently high positive velocity or a max velocity exceeding threshold
                    if velocities and max(velocities) >= 4:
                        is_fall = True

            onset.append(idx_val / FS)
            duration.append(0)
            
            if is_fall:
                trial_type.append("Hit/fall")
            else:
                trial_type.append("Hit/life_lost")
                
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_bricks_smashed_events(repvars, FS=60):
    """Generate events for when Mario smashes bricks.

    Detected by score increasing by 5 points while airborne (jump_airborne == 1).

    Parameters
    ----------
    repvars : dict
        Dictionary containing all the variables of a single repetition
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df : pandas.DataFrame
        Events DataFrame in BIDS-compatible format
    """

    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    score_increments = list(np.diff(repvars["score"]))
    for idx_val, inc in enumerate(score_increments):
        if inc == 5:
            if repvars["jump_airborne"][idx_val] == 1:
                onset.append(idx_val / FS)
                duration.append(0)
                trial_type.append("Brick_smashed")
                level.append(repvars["level"])
                frame_start.append(idx_val)
                frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_coin_events(repvars, FS=60):
    """Generate events for coin collection.

    Detected by increase in coins counter.

    Parameters
    ----------
    repvars : dict
        Dictionary containing all the variables of a single repetition
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df : pandas.DataFrame
        Events DataFrame in BIDS-compatible format
    """
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    diff_coins = np.diff(repvars["coins"])
    for idx_val, val in enumerate(diff_coins):
        if val > 0:
            onset.append(idx_val / FS)
            duration.append(0)
            trial_type.append("Coin_collected")
            level.append(repvars["level"])
            frame_start.append(idx_val)
            frame_stop.append(idx_val)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def generate_powerup_events(repvars, FS=60):
    """Generate events for powerup collection.

    Detected by player_state being in [9, 12, 13] which indicates
    the animation of collecting a powerup.

    Parameters
    ----------
    repvars : dict
        Dictionary containing all the variables of a single repetition
    FS : int
        The sampling rate of the .bk2 file

    Returns
    -------
    events_df : pandas.DataFrame
        Events DataFrame in BIDS-compatible format
    """
    onset = []
    duration = []
    trial_type = []
    level = []
    frame_start = []
    frame_stop = []

    # powerup collect events
    for idx, val in enumerate(repvars["player_state"][:-1]):
        if val in [9, 12, 13]:
            if repvars["player_state"][idx + 1] != val:
                onset.append(idx / FS)
                duration.append(0)
                trial_type.append("Powerup_collected")
                level.append(repvars["level"])
                frame_start.append(idx)
                frame_stop.append(idx)

    events_df = pd.DataFrame(
        data={
            "onset": onset,
            "duration": duration,
            "trial_type": trial_type,
            "level": level,
            "frame_start": frame_start,
            "frame_stop": frame_stop,
        }
    )
    return events_df


def main(args):
    FS = 60

    # Get datapath
    DATA_PATH = args.datapath
    if DATA_PATH == ".":
        print("No data path specified. Searching files in this folder.")
    print(f"Generating annotations for the mario dataset in : {DATA_PATH}")

    OUTPUT_PATH = args.output_path

    # Get subject/session filters
    subjects = args.subjects
    sessions = args.sessions

    if subjects:
        print(f"Filtering subjects: {', '.join(subjects)}")
    if sessions:
        print(f"Filtering sessions: {', '.join(sessions)}")

    # Walk through all folders looking for events.tsv files
    for root, folder, files in sorted(os.walk(DATA_PATH)):
        if not "sourcedata" in root:
            # Check if this path matches subject filter
            if subjects is not None:
                if not any(sub in root for sub in subjects):
                    continue

            # Check if this path matches session filter
            if sessions is not None:
                if not any(ses in root for ses in sessions):
                    continue

            for file in files:
                if "events.tsv" in file and not "annotated" in file:
                    run_events_file = op.join(root, file)
                    run_id = file.split("_")[3]
                    if OUTPUT_PATH is not None:
                        sub = file.split("_")[0]
                        ses = file.split("_")[1]
                        events_annotated_fname = op.join(
                            OUTPUT_PATH,
                            sub,
                            ses,
                            "func",
                            file.replace("_events.", "_desc-annotated_events."),
                        )
                        os.makedirs(op.dirname(events_annotated_fname), exist_ok=True)
                    else:
                        events_annotated_fname = run_events_file.replace(
                            "_events.", "_desc-annotated_events."
                        )
                    if not op.isfile(events_annotated_fname):
                        print(f"Processing : {file}")
                        events_dataframe = pd.read_table(run_events_file, index_col=0)
                        events_dataframe = events_dataframe[
                            events_dataframe["trial_type"] == "gym-retro_game"
                        ]  # select only repetition events
                        events_dataframe = events_dataframe[
                            ["trial_type", "onset", "level", "stim_file"]
                        ].reset_index()  # select only relevant columns
                        bk2_files = events_dataframe["stim_file"].values.tolist()
                        runvars = []
                        for bk2_idx, bk2_file in enumerate(bk2_files):
                            if bk2_file != "Missing file" and type(bk2_file) != float:
                                print("Adding : " + bk2_file)
                                sub = bk2_file.split("/")[0]
                                ses = bk2_file.split("/")[1]
                                filename = bk2_file.split("/")[-1]
                                # Look for variables file in gamelogs/ within datapath
                                variables_sidecar_fname = op.join(
                                    DATA_PATH,
                                    sub,
                                    ses,
                                    "gamelogs",
                                    filename.replace(".bk2", "_variables.json"),
                                )
                                if op.exists(variables_sidecar_fname):
                                    with open(variables_sidecar_fname, "r") as f:
                                        repvars = json.load(f)

                                    # Add info to repetition event
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "level",
                                    ] = repvars[
                                        "level"
                                    ]  # replace level value in the dataframe by the one in the repvars dict
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "frame_start",
                                    ] = int(0)
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "frame_stop",
                                    ] = int(len(repvars["score"]))
                                    events_dataframe.loc[
                                        events_dataframe["stim_file"] == bk2_file,
                                        "duration",
                                    ] = (
                                        int(len(repvars["score"])) / FS
                                    )

                                    # rename index column to rep_index and ensure 1-based sequential
                                    events_dataframe["rep_index"] = range(1, len(events_dataframe) + 1)

                                    runvars.append(repvars)
                                else:
                                    print(f"\nError: Variables file not found: {variables_sidecar_fname}")
                                    print("Please run create_replays.py first to generate the required files.")
                                    return
                            else:
                                print("Missing file, skipping")
                                runvars.append({})

                        # Add phase (discovery VS practice)
                        if (
                            events_dataframe["level"].values[0]
                            == events_dataframe["level"].values[1]
                        ):
                            phase = "discovery"
                        else:
                            phase = "practice"
                        events_dataframe["phase"] = phase
                        events_df = create_runevents(
                            runvars, run_id, events_dataframe, FS=FS
                        )

                        events_df.to_csv(events_annotated_fname, sep="\t", index=False)
                        print(f"Saved annotated events to: {events_annotated_fname}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--datapath",
        default=".",
        type=str,
        help="Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.",
    )

    parser.add_argument(
        "-o",
        "--output_path",
        default=None,
        type=str,
        help="Path to save the annotated events files. If not specified, saves in the same folder as the input events.tsv files.",
    )

    parser.add_argument(
        "--subjects",
        "-sub",
        nargs="+",
        default=None,
        help="List of subjects to process (e.g., sub-01 sub-02). If not specified, all subjects are processed.",
    )

    parser.add_argument(
        "--sessions",
        "-ses",
        nargs="+",
        default=None,
        help="List of sessions to process (e.g., ses-001 ses-002). If not specified, all sessions are processed.",
    )

    args = parser.parse_args()
    main(args)
