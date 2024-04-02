### This script is used to generate annotated event_files for the mario dataset from the pkl sidecars.

import argparse
import os
import os.path as op
import retro
import pandas as pd
import pickle
import numpy as np

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
    default='./stimuli',
    type=str,
    help="Data path to look for the stimuli files (rom, state files, data.json etc...).",
)


def create_runevents(runvars, events_dataframe, FS=60):
    """Create a BIDS compatible events dataframe from game variables and start/duration info of repetitions

    Parameters
    ----------
    runvars : list
        A list of repvars dicts, corresponding to the different repetitions of a run. Each repvar must have it's own duration and onset.
    events_dataframe : pandas.DataFrame
        A BIDS-formatted DataFrame specifying the onset and duration of each repetition.
    FS : int
        The sampling rate of the .bk2 file
    get_actions : boolean
        If True, generates actions events based on key presses
    get_healthloss : boolean
        If True, generates health loss events based on changes on the "lives" variable
    get_kills : boolean
        If True, generates events indicating when an enemy has been killed (based on score increase)

    Returns
    -------
    events_df :
        An events DataFrame in BIDS-compatible format.
    """
    all_df = [events_dataframe]
    for idx, repvars in enumerate(runvars):
        n_frames_total = len(repvars['START'])
        repvars['rep_onset'] = [events_dataframe['onset'][idx]]
        repvars['rep_duration'] = n_frames_total / FS

        if len(repvars.keys()) > 0: # Check if repetition logs are available
            # Actions
            ACTIONS = ['UP', 'DOWN', 'LEFT', 'RIGHT', 'A', 'B', 'START', 'SELECT']
            for act in ACTIONS:
                temp_df = generate_key_events(repvars, act, FS=FS)
                temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
                all_df.append(temp_df)

            # Kills
            temp_df = generate_kill_events(repvars, FS=FS)
            temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
            all_df.append(temp_df)

            # Hits taken
            temp_df = generate_hits_taken_events(repvars, FS=FS)
            temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
            all_df.append(temp_df)

            # Bricks smashed
            temp_df = generate_bricks_smashed_events(repvars, FS=FS)
            temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
            all_df.append(temp_df)

            # Coins collected
            temp_df = generate_coin_events(repvars, FS=FS)
            temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
            all_df.append(temp_df)
            
            # Powerups
            temp_df = generate_powerup_events(repvars, FS=FS)
            temp_df['onset'] = temp_df['onset'] + repvars['rep_onset']
            all_df.append(temp_df)

    try:
        events_df = pd.concat(all_df).sort_values(by='onset').reset_index(drop=True)
    except ValueError:
        print('No bk2 files available for this run. Returning empty df.')
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
    presses = [round(i/FS, 3) for i, x in enumerate(diffs) if x == 1]
    releases = [round(i/FS, 3) for i, x in enumerate(diffs) if x == -1]
    onset = presses
    level = [repvars["level"] for x in onset]
    duration = [round(releases[i] - presses[i], 3) for i in range(len(presses))]
    trial_type = ['{}'.format(key) for i in range(len(presses))]
    events_df = pd.DataFrame(data={'onset':onset,
                                   'duration':duration,
                                   'trial_type':trial_type,
                                   'level':level})
    return events_df

def generate_kill_events(repvars, FS=60):
    """ Create a BIDS compatible events dataframe containing kill events.
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

    killvals_dict = {4:'stomp',
                     34:'impact',
                     132:'kick'}

    n_frames_total = len(repvars['START'])
    for frame_idx in range(n_frames_total-1):
        for ii in range(6):
            curr_val = repvars[f'enemy_kill3{ii}'][frame_idx]
            next_val = repvars[f'enemy_kill3{ii}'][frame_idx+1]
            if curr_val in [4, 34, 132] and curr_val != next_val:
                killstring = f'Kill/{killvals_dict[curr_val]}'
                if ii == 5:
                    if repvars['powerup_yes_no'] == 0:
                        onset.append(frame_idx/FS)
                        duration.append(0)
                        trial_type.append(killstring)
                        level.append(repvars['level'])
                else:
                    onset.append(frame_idx/FS)
                    duration.append(0)
                    trial_type.append(killstring)
                    level.append(repvars['level'])

    events_df = pd.DataFrame(data={'onset':onset,
                               'duration':duration,
                               'trial_type':trial_type,
                               'level':level})
    return events_df

def generate_hits_taken_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []

    # Powerup lost
    diff_state = list(np.diff(repvars['powerstate']))
    for idx_val, val in enumerate(diff_state):
        if val < -10000:
            onset.append(idx_val/FS)
            duration.append(0)
            trial_type.append('Hit/powerup_lost')
            level.append(repvars['level'])

    # Lives lost
    diff_lives = list(np.diff(repvars['lives']))
    for idx_val, val in enumerate(diff_lives):
        if val < 0:
            onset.append(idx_val/FS)
            duration.append(0)
            trial_type.append('Hit/life_lost')
            level.append(repvars['level'])

    events_df = pd.DataFrame(data={'onset':onset,
                            'duration':duration,
                            'trial_type':trial_type,
                            'level':level})
    return events_df

def generate_bricks_smashed_events(repvars, FS=60):

    onset = []
    duration = []
    trial_type = []
    level = []

    score_increments = list(np.diff(repvars['score']))
    for idx_val, inc in enumerate(score_increments):
        if inc == 5:
            if repvars['jump_airborne'][idx_val] == 1:
                onset.append(idx_val/FS)
                duration.append(0)
                trial_type.append('Brick_smashed')
                level.append(repvars['level'])

    events_df = pd.DataFrame(data={'onset':onset,
                               'duration':duration,
                               'trial_type':trial_type,
                               'level':level})
    return events_df

def generate_coin_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []
    
    diff_coins = np.diff(repvars['coins'])
    for idx_val, val in enumerate(diff_coins):
        if val > 0:
            onset.append(idx_val/FS)
            duration.append(0)
            trial_type.append('Coin_collected')
            level.append(repvars['level'])

    events_df = pd.DataFrame(data={'onset':onset,
                               'duration':duration,
                               'trial_type':trial_type,
                               'level':level})
    return events_df

def generate_powerup_events(repvars, FS=60):
    onset = []
    duration = []
    trial_type = []
    level = []

    ''' ### Currently broken
    diff_powerup = np.diff(repvars['powerup_yes_no'])
    # powerup on screen events
    for idx, val in enumerate(repvars['powerup_yes_no'][:-1]):
        if val == 46:
            idx_stop = idx
            while diff_powerup[idx_stop] != -46:
                idx_stop += 1
            onset.append(idx/FS)
            duration.append((idx_stop-idx)/FS)
            trial_type.append('Powerup_on_screen')
            level.append(repvars['level'])
    '''
    # powerup collect events
    for idx, val in enumerate(repvars['player_state'][:-1]):
        if val in [9,12,13]:
            if repvars['player_state'][idx+1] != val:
                onset.append(idx/FS)
                duration.append(0)
                trial_type.append('Powerup_collected')
                level.append(repvars['level'])
    
    events_df = pd.DataFrame(data={'onset':onset,
                               'duration':duration,
                               'trial_type':trial_type,
                               'level':level})
    return events_df

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
                    events_annotated_fname = run_events_file.replace("_events.", "_desc-annotated_events.")
                    if not op.isfile(events_annotated_fname):
                        print(f"Processing : {file}")
                        events_dataframe = pd.read_table(run_events_file, index_col=0)
                        events_dataframe = events_dataframe[events_dataframe['trial_type']=='gym-retro_game'] # select only repetition events
                        events_dataframe = events_dataframe[['trial_type','onset', 'level', 'stim_file']] # select only relevant columns

                        bk2_files = events_dataframe['stim_file'].values.tolist()
                        runvars = []
                        for bk2_idx, bk2_file in enumerate(bk2_files):
                            if bk2_file != "Missing file" and type(bk2_file) != float:
                                print("Adding : " + bk2_file)
                                if op.exists(bk2_file):
                                    pkl_sidecar_fname = bk2_file.replace(".bk2", ".pkl")
                                    with open(pkl_sidecar_fname, 'rb') as f:
                                        repvars = pickle.load(f)
                                    events_dataframe.loc[events_dataframe['stim_file']==bk2_file, 'level'] = repvars['level'] # replace level value in the dataframe by the one in the repvars dict
                                    runvars.append(repvars)
                            else:
                                print("Missing file, skipping")
                                runvars.append({})
                        events_df = create_runevents(runvars, events_dataframe)
                        events_df.to_csv(events_annotated_fname, sep='\t', index=False)

if __name__ == "__main__":
    args = parser.parse_args()
    main(args)