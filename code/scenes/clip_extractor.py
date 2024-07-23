### Extract clips from mario dataset
#
# This script is used to extract clips from the mario dataset, based on the scenes file.
# The scenes file is a JSON file that contains the start and end positions of the patterns to clip.
# The script will walk through the dataset and look for .bk2 files, then replay them and extract the frames that correspond to the start and end positions of the patterns.
# The clips are then saved as .gif files in the output folder.
# /!\ To work properly, the script needs to be run on the root of the mario dataset, and the stimuli folder should be in the same folder as the script.
# /!\ If you have "Could not load movie" error, run the script FROM the root of the mario dataset directly. 
# Make sure that the mario dataset is on the branch "events", that the stimuli folder have been downloaded as well as the .bk2 and events.tsv files from the dataset.
# The script can be run from the command line with the following arguments:
# - `datapath` : Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.
# - `output` : Path to the output folder, where the clips will be saved. By default it will be in the root dataset.
# - `scenesfile` : Path to the scenes file, a JSON file that contains info about the start and end positions to clip.
#
# Example:
# python clip_extractor.py -d /path/to/mario/dataset -o /path/to/output/folder -s /path/to/scenes.json

import argparse
import os
import os.path as op
import retro
import pandas as pd
import json
import numpy as np
import pickle
import skvideo.io
from retro.scripts.playback_movie import playback_movie
from numpy import load
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--datapath",
    default='.',
    type=str,
    help="Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.",
)
parser.add_argument(
    "-o",
    "--output",
    default=None,
    type=str,
    help="Path to the output folder, where the clips will be saved.",
)

parser.add_argument(
    "-s",
    "--scenesfile",
    default=None,
    type=str,
    help="Path to the scenes file, a JSON file that contains info about the start and end positions to clip.",
)

parser.add_argument(
    "-ext",
    "--clip_extension",
    default="gif",
    type=str,
    help="Format in which the extracted clips should be save"
)


def replay_bk2(
    bk2_path, skip_first_step=True, game=None, scenario=None, inttype=retro.data.Integrations.CUSTOM_ONLY
):
    """Make an iterator that replays a bk2 file, returning frames, keypresses and annotations.

    Example
    -------
    ```Data path to look for the stimuli files (rom, state files, data.json etc...).(path):
        all_frames.append(frame)
        all_keys.append(keys)
    ```

    Parameters
    ----------
    bk2_path : str
        Path to the bk2 file to replay.
    skip_first_step : bool
        Whether to skip the first step before starting the replay. The intended use of
        gym retro is to do so (i.e. True) but if the recording was not initiated as intended
        per gym-retro, not skipping (i.e. False) might be required. Default is True.
    scenario : str
        Path to the scenario json file. If None, the scenario.json file in the game integration
        folder will be used. Default is None.
    inttype : gym-retro Integration
        Type of gym-retro integration to use. Default is `retro.data.Integrations.CUSTOM_ONLY`
        for custom integrations, for default integrations shipped with gym-retro, use
        `retro.data.Integrations.STABLE`.

    Yields
    -------
    frame : numpy.ndarray
        Current frame of the replay, of shape (H,W,3).
    keys : list of bool
        Current keypresses, list of booleans stating whicn key is pressed or not. The ordered name
        of the keys is in `emulator.buttons`.
    annotations : dict
        Dictonary containing the annotations of the game : reward, done condition and the values of
        the variables that are extracted from the emulator's memory.
    sound : dict
        Dictionnary containing the sound output from the game : audio and audio_rate.
    """
    movie = retro.Movie(bk2_path)
    if game == None:
        game = movie.get_game()
    emulator = retro.make(game, scenario=scenario, inttype=inttype, render_mode=None)
    emulator.initial_state = movie.get_state()
    actions = emulator.buttons
    emulator.reset()
    if skip_first_step:
        movie.step()
    while movie.step():
        keys = []
        for p in range(movie.players):
            for i in range(emulator.num_buttons):
                keys.append(movie.get_key(i, p))
        frame, rew, terminate, truncate, info = emulator.step(keys)
        sound = {"audio": emulator.em.get_audio(), "audio_rate": emulator.em.get_audio_rate()}
        annotations = {"reward": rew, "done": terminate, "info": info}
        yield frame, keys, annotations, sound, actions
    emulator.close()


def get_variables_from_replay(bk2_fpath, skip_first_step, game=None, scenario=None, inttype=retro.data.Integrations.CUSTOM_ONLY):
    """Replay the file and returns a formatted dict containing game variables.

    Parameters
    ----------
    bk2_fpath : str
        Full path to the bk2 file
    skip_first_step : bool
        Remove first step of replay if necessary.
    save_gif : bool, optional
        Saves a gif of the replay in the parent folder, by default False
    duration : int, optional
        Duration of a frame in the gif file, by default 10
    game : str, optional
        Game name, defaults to movie.get_game(), by default None
    scenario : str, optional
        Scenario name, by default None
    inttype : gym-retro Integration, optional
        Integration specification, can be STABLE or CUSTOM_ONLY, by default retro.data.Integrations.CUSTOM_ONLY

    Returns
    -------
    dict
        Dictionnary of game variables, as specified in the data.json file. Each entry is a list with one value per frame.
    """
    replay = replay_bk2(bk2_fpath, skip_first_step=skip_first_step, game=game, scenario=scenario, inttype=inttype)
    all_frames = []
    all_keys = []
    all_info = []
    for frame, keys, annotations, sound, actions in replay:
        all_keys.append(keys)
        all_info.append(annotations["info"])
        all_frames.append(frame)
    repetition_variables = reformat_info(all_info, all_keys, bk2_fpath, actions)

    if annotations['done'] != True:
        print(f"Warning : done condition have not been satisfied, try changing the value of skip_first_frame.")
                                         
    return repetition_variables, all_frames

def reformat_info(info, keys, bk2_fpath, actions):
    """Create dict structure from info extracted during the replay.

    Parameters
    ----------
    info : list
        List of info (one per replay frame)
    keys : list
        List of keys (one per replay frame)
    bk2_fpath : str'/home/hyruuk/DATA/mario/pattern_clips'
        Full path to the bk2
    game : str, optional
        Game name, by default None

    Returns
    -------
    dict
        Dict structure with one entry per variable, each entry is a list with one value per frame.
    """
    repetition_variables = {}
    repetition_variables["filename"] = bk2_fpath
    repetition_variables["level"] = bk2_fpath.split("/")[-1].split("_")[-2]
    repetition_variables["subject"] = bk2_fpath.split("/")[-1].split("_")[0]
    repetition_variables["session"] = bk2_fpath.split("/")[-1].split("_")[1]
    repetition_variables["repetition"] = bk2_fpath.split("/")[-1].split("_")[-1].split(".")[0]

    repetition_variables["actions"] = actions
    

    for key in info[0].keys():
        repetition_variables[key] = []
    for button in repetition_variables["actions"]:
        repetition_variables[button] = []
    
    for frame_idx, frame_info in enumerate(info):
        for key in frame_info.keys():
            repetition_variables[key].append(frame_info[key])
        for button_idx, button in enumerate(repetition_variables["actions"]):
            repetition_variables[button].append(keys[frame_idx][button_idx])
    
    return repetition_variables

def correct_xscroll(scenes_info):
    '''Correct xscroll from Hi and Lo to a single value.
    '''
    for level in scenes_info.keys():
        for pattern in scenes_info[level].keys():
            for position in scenes_info[level][pattern]:
                scenes_info[level][pattern][position]['xscroll'] = scenes_info[level][pattern][position]['xscrollHi']*256 + scenes_info[level][pattern][position]['xscrollLo']
    return scenes_info


def make_gif(selected_frames, movie_fname):
    frame_list = [Image.fromarray(np.uint8(img), "RGB") for img in selected_frames]

    if len(frame_list) < 1:
        print(f"No frames to save in {movie_fname}")
        return
    
    frame_list[0].save(movie_fname, save_all=True, append_images=frame_list[1:], optimize=False, duration=16, loop=0)


def make_mp4(selected_frames, movie_fname):
    writer = skvideo.io.FFmpegWriter(
        movie_fname, inputdict={"-r": "60"}, outputdict={"-r": "60"}
    )
    for frame in selected_frames:
        im = Image.new("RGB", (frame.shape[1], frame.shape[0]), color="white")
        im.paste(Image.fromarray(frame), (0, 0))
        writer.writeFrame(np.array(im))
    writer.close()


def main(args):
    # Get datapath
    DATA_PATH = os.path.abspath(args.datapath)
    
    # Load scenes info
    SCENES_FILE = args.scenesfile
    if SCENES_FILE is None:
        SCENES_FILE = op.join(DATA_PATH, "scenes.json")
    SCENES_FILE = op.join(DATA_PATH, "code", "scenes","scenes_mastersheet.csv")

    scenes_info = pd.read_csv(SCENES_FILE)

    #scenes_info = correct_xscroll(scenes_info)
    scenes_info_dict = {}
    for idx, row in scenes_info.iterrows():
        scene_id = f'w{row["World"]}l{row["Level"]}s{row["Scene"]}'
        scenes_info_dict[scene_id] = {}
        scenes_info_dict[scene_id]['start'] = row['Entry point']
        scenes_info_dict[scene_id]['end'] = row['Exit point']
        scenes_info_dict[scene_id]['level_layout'] = row['Level layout']

    # Setup output folder
    CLIPS_FOLDER = args.output
    if CLIPS_FOLDER is None:
        CLIPS_FOLDER = op.join(DATA_PATH, "pattern_clips")
        os.makedirs(CLIPS_FOLDER, exist_ok=True)

    # Integrate game
    os.chdir(DATA_PATH)
    STIMULI_PATH = op.join(DATA_PATH, "stimuli")
    retro.data.Integrations.add_custom_path(STIMULI_PATH)
    

    print(f'Generating annotations for the mario dataset in : {DATA_PATH}')
    print(f'Taking stimuli from : {STIMULI_PATH}')
    print(f'Saving clips in : {CLIPS_FOLDER}')
    print(f'Using scenes file : {SCENES_FILE}')
    

    #### TODO :
    ### - Find a way to avoid bonus scenes being confused with regular scenes (ie w1l1s0 and w1l1s12)
    subjects = []
    clip_codes = []
    clip_bounds = []
    clip_vars = []
    clip_scenes = []

    # Walk through all folders looking for .bk2 files
    for root, folder, files in sorted(os.walk(DATA_PATH)):
        if not "sourcedata" in root:
            for file in files:
                if "events.tsv" in file and not "annotated" in file:
                    run_events_file = op.join(root, file)
                    print(f"Processing : {file}")
                    events_dataframe = pd.read_table(run_events_file)
                    events_dataframe = events_dataframe[events_dataframe['trial_type'] == 'gym-retro_game']
                    sub = run_events_file.split("_")[0].split('/')[-1]
                    ses = run_events_file.split("_")[1].split("-")[1]
                    run = run_events_file.split("_")[-2].split("-")[1]
                    bk2_files = events_dataframe['stim_file'].values.tolist()
                    for bk2_idx, bk2_file in enumerate(bk2_files):
                        if bk2_file != "Missing file" and type(bk2_file) != float:
                            print("Checking : " + bk2_file)
                            rep_order_string = f'{str(ses).zfill(3)}{str(run).zfill(2)}{str(bk2_idx).zfill(2)}'
                            curr_level = bk2_file.split("/")[-1].split("_")[-2].split('-')[1]
                            if curr_level == 'w1l1': ## remove/replace later
                                repvars, frames_list = get_variables_from_replay(bk2_file, skip_first_step=bk2_idx==0, inttype=retro.data.Integrations.CUSTOM_ONLY)
                                # Get some info about current repetition
                                n_frames_total = len(frames_list)
                                # Create player_x_pos from Hi and Lo
                                repvars['player_x_pos'] = []
                                for idx in range(n_frames_total):
                                    repvars['player_x_pos'].append(repvars['player_x_posHi'][idx]*256 + repvars['player_x_posLo'][idx])
                                
                                # Look for clips
                                for current_scene in scenes_info_dict.keys():
                                    print(current_scene)
                                    scenes_info_found = []
                                    print(f'Scene {current_scene} : start = {scenes_info_dict[current_scene]["start"]}, end = {scenes_info_dict[current_scene]["end"]}')
                                    start_found = False
                                    ## TODO manage issue with bonus scenes
                                    for frame_idx in range(1, n_frames_total):
                                        if not start_found:
                                            # Look for start
                                            if (repvars['player_x_pos'][frame_idx] >= scenes_info_dict[current_scene]['start'] and 
                                                repvars['player_x_pos'][frame_idx-1] < scenes_info_dict[current_scene]['start'] and 
                                                repvars['player_x_pos'][frame_idx] < scenes_info_dict[current_scene]['end'] and 
                                                repvars['level_layout'][frame_idx] == scenes_info_dict[current_scene]['level_layout']):
                                                start_idx = frame_idx
                                                start_found = True
                                        else:
                                            # Look for end
                                            if (repvars['player_x_pos'][frame_idx] >= scenes_info_dict[current_scene]['end'] and 
                                                repvars['player_x_pos'][frame_idx-1] < scenes_info_dict[current_scene]['end']):
                                                end_idx = frame_idx
                                                start_found = False
                                                scenes_info_found.append([start_idx, end_idx])
                                            elif (repvars['player_x_pos'][frame_idx] >= scenes_info_dict[current_scene]['start'] and 
                                                  repvars['player_x_pos'][frame_idx-1] < scenes_info_dict[current_scene]['start']):
                                                start_idx = frame_idx

                                    print(f'scenes_info found for {current_scene} : {scenes_info_found}')
                                    for pat_idx, pattern in enumerate(scenes_info_found):
                                        start_idx, end_idx = pattern
                                        selected_frames = frames_list[start_idx:end_idx]
                                        clip_code = f'{rep_order_string}{str(start_idx).zfill(7)}'
                                        assert len(clip_code) == 14, print(rep_order_string, start_idx)
                                        clip_fname = op.join(CLIPS_FOLDER, f"{repvars['subject']}_{repvars['session']}_{repvars['level']}_{repvars['repetition']}_scene-{current_scene.split('s')[1]}_code-{clip_code}.{args.clip_extension}")
                                        if args.clip_extension == 'gif':
                                            make_gif(selected_frames, clip_fname)
                                        elif args.clip_extension in ['mp3', 'mp4']:
                                            make_mp4(selected_frames, clip_fname)
                                        subjects.append(sub)
                                        clip_codes.append(clip_code)
                                        clip_bounds.append(pattern)
                                        clip_scenes.append(current_scene.split('s')[1])
                                        clip_variables = {}
                                        for key in repvars.keys():
                                            if len(repvars[key]) == n_frames_total:
                                                clip_variables[key] = repvars[key][start_idx:end_idx]
                                            else:
                                                clip_variables[key] = repvars[key]
                                        clip_vars.append(clip_variables)

    # Save clip data in a pickle object
    clip_data = {
        'subjects': subjects,
        'clip_codes': clip_codes,
        'clip_bounds': clip_bounds,
        'clip_vars': clip_vars,
        'clip_scenes': clip_scenes
    }
    with open(op.join(CLIPS_FOLDER, "clip_data.pkl"), "wb") as f:
        pickle.dump(clip_data, f)

                
if __name__ == "__main__":

    args = parser.parse_args()
    main(args)