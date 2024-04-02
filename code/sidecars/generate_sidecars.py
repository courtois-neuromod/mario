### This script is used to generate json sidecar files and playback videos for the mario dataset.

import argparse
import os
import os.path as op
import retro
import pandas as pd
import json
import numpy as np
import pickle
from retro.scripts.playback_movie import playback_movie
from numpy import load

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--datapath",
    default='.',
    type=str,
    help="Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.",
)
parser.add_argument(
    "-s",
    "--stimuli",
    default=None,
    type=str,
    help="Data path to look for the stimuli files (rom, state files, data.json etc...).",
)

def count_kills(repvars):
    kill_count = 0
    for i in range(6):
        for idx, val in enumerate(repvars[f'enemy_kill3{i}'][:-1]):
            if val in [4, 34, 132]:
                if repvars[f'enemy_kill3{i}'][idx+1] != val:
                    if i == 5:
                        if repvars['powerup_yes_no'] == 0:
                            kill_count += 1
                    else:
                        kill_count += 1
    return kill_count

def count_bricks_destroyed(repvars):
    score_increments = list(np.diff(repvars['score']))
    bricks_destroyed = 0
    for idx, inc in enumerate(score_increments):
        if inc == 5:
            if repvars['jump_airborne'][idx] == 1:
                bricks_destroyed += 1
    return bricks_destroyed

def count_hits_taken(repvars):
    diff_state = list(np.diff(repvars['powerstate']))
    # count powerups lost
    hits_count = 0
    for idx, val in enumerate(diff_state):
        if val < -10000:
            hits_count += 1

    # count lives lost
    diff_lives = list(np.diff(repvars['lives']))
    for idx, val in enumerate(diff_lives):
        if val < 0:
            hits_count += 1
    return hits_count

def count_powerups_collected(repvars):
    powerup_count = 0
    for idx, val in enumerate(repvars['player_state'][:-1]):
        if val in [9,12,13]:
            if repvars['player_state'][idx+1] != val:
                powerup_count += 1
    return powerup_count

def create_info_dict(repvars):
    info_dict = {}

    # world
    info_dict['world'] = repvars['level'][1]

    # level
    info_dict['level'] = repvars['level'][-1]

    # duration
    info_dict['duration'] = len(repvars['score']) / 60

    # terminated
    info_dict['terminated'] = repvars['terminate'][-1]==True

    # cleared
    info_dict['cleared'] = all([repvars['terminate'][-1]==True, repvars['lives'][-1] >= 0])

    # final_score
    info_dict['final_score'] = repvars['score'][-1]

    # final_position
    # Position is encoded by these two variables. I assume that xscrollHi starts at 1 and is incremented
    # by 1 everytime xscrollLo reaches 256.
    info_dict['final_position'] = repvars['xscrollLo'][-1] + (256*(repvars['xscrollHi'][-1]))

    # lives_lost
    info_dict['lives_lost'] = 2 - repvars['lives'][-1]

    # hits taken
    info_dict['hits_taken'] = count_hits_taken(repvars)

    # number of enemies killed
    info_dict['enemies_killed'] = count_kills(repvars)

    # number of powerups collected
    info_dict['powerups_collected'] = count_powerups_collected(repvars)

    # number of bricks destroyed
    info_dict['bricks_destroyed'] = count_bricks_destroyed(repvars)

    # number of coins collected
    info_dict['coins'] = repvars['coins'][-1]

    return info_dict

def format_repvars_dict(bk2_file, emulator):
    npy_file = bk2_file.replace(".bk2", ".npz")
    with load(npy_file, allow_pickle=True) as data:
        info = data['info']
        actions = data['actions']
    
    repvars = {}
    # Fill variables
    for key in info[0].keys():
        repvars[key] = []
    for frame in info:
        for key in repvars.keys():
            repvars[key].append(frame[key])
    # Fill actions
    for idx_button, button in enumerate(emulator.buttons):
        repvars[button] = []
        for frame in actions:
            repvars[button].append(frame[idx_button])

    repvars["filename"] = bk2_file
    repvars["level"] = bk2_file.split("/")[-1].split("_")[-2].split('-')[1]
    repvars["subject"] = bk2_file.split("/")[-1].split("_")[0]
    repvars["session"] = bk2_file.split("/")[-1].split("_")[1]
    repvars["repetition"] = bk2_file.split("/")[-1].split("_")[-1].split(".")[0]
    repvars["terminate"] = [True] # ... I don't know how to get this info from the playback_movie function or the emulator object
        
    return repvars

def main(args):
    # Get datapath
    DATA_PATH = args.datapath
    if DATA_PATH == ".":
        print("No data path specified. Searching files in this folder.")
    print(f'Generating annotations for the mario dataset in : {DATA_PATH}')
    # Import stimuli
    if args.stimuli is None:
        print("No stimuli path specified. Searching files in this folder.")
        stimuli_path = op.join(os.getcwd(), "stimuli")
        print(stimuli_path)
    else:
        stimuli_path = op.join(args.stimuli)
    retro.data.Integrations.add_custom_path(stimuli_path)
    
    # Walk through all folders looking for .bk2 files
    for root, folder, files in sorted(os.walk(DATA_PATH)):
        if not "sourcedata" in root:
            for file in files:
                if "events.tsv" in file and not "annotated" in file:
                    run_events_file = op.join(root, file)
                    print(f"Processing : {file}")
                    events_dataframe = pd.read_table(run_events_file)
                    bk2_files = events_dataframe['stim_file'].values.tolist()
                    for bk2_idx, bk2_file in enumerate(bk2_files):
                        if bk2_file != "Missing file" and type(bk2_file) != float:
                            print("Adding : " + bk2_file)
                            if op.exists(bk2_file):
                                if not op.exists(bk2_file.replace(".bk2", ".json")):
                                    # replay and save using retro legacy function
                                    # This bloc is important to get the skip_first_step right before playback_movie
                                    game = None
                                    scenario = None
                                    inttype = retro.data.Integrations.CUSTOM_ONLY
                                    movie = retro.Movie(bk2_file)
                                    skip_first_step = bk2_idx==0
                                    if game == None:
                                        game = movie.get_game()
                                    emulator = retro.make(game, scenario=scenario, inttype=inttype, render_mode=False)
                                    emulator.initial_state = movie.get_state()
                                    emulator.reset()
                                    if skip_first_step:
                                        movie.step()

                                    npy_file = bk2_file.replace(".bk2", ".npz")
                                    video_file = bk2_file.replace(".bk2", ".mp4")
                                    playback_movie(emulator, movie, npy_file=npy_file, video_file=video_file, lossless='mp4', info_file=True)
                                    emulator.close()

                                    repvars = format_repvars_dict(bk2_file, emulator)

                                    info_dict = create_info_dict(repvars)

                                    # write info_dict to json file
                                    json_sidecar_fname = bk2_file.replace(".bk2", ".json")
                                    with open(json_sidecar_fname, 'w') as f:
                                        json.dump(info_dict, f)

                                    # write repvars dict as pkl
                                    pkl_sidecar_fname = bk2_file.replace(".bk2", ".pkl")
                                    with open(pkl_sidecar_fname, 'wb') as f:
                                        pickle.dump(repvars, f)
                                    
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)