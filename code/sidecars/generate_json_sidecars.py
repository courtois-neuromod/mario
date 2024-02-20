import argparse
import os
import os.path as op
from videogames_tools.replay.replay import get_variables_from_replay
import retro
import pandas as pd

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


def create_info_dict(repvars):
    info_dict = {}
    return info_dict

def main(args):
    # Get datapath
    DATA_PATH = args.datapath
    if DATA_PATH == ".":
        print("No data path specified. Searching files in this folder.")
    print('Generating annotations for the mario dataset in : {DATA_PATH}')
    # Import stimuli
    stimuli_path = op.join(args.stimuli)
    # stimuli_path = '/home/hyruuk/GitHub/neuromod/mario.stimuli/SuperMarioBros-Nes'
    retro.data.Integrations.add_custom_path(stimuli_path)
    # Walk through all folders looking for .bk2 files
    for root, folder, files in os.walk(DATA_PATH):
        if not "sourcedata" in root:
            for file in files:
                if "events.tsv" in file and not "annotated" in file:
                    run_events_file = op.join(root, file)
                    events_annotated_fname = run_events_file.replace("_events.", "_desc-annotated_events.")
                    if not op.isfile(events_annotated_fname):
                        print(f"Processing : {file}")
                        events_dataframe = pd.read_table(run_events_file)
                        bk2_files = events_dataframe['stim_file'].values.tolist()
                        runvars = []
                        for bk2_idx, bk2_file in enumerate(bk2_files):
                            if bk2_file != "Missing file" and type(bk2_file) != float:
                                print("Adding : " + bk2_file)
                                #bk2_fname = op.join(DATA_PATH, bk2_file)
                                if op.exists(bk2_file):
                                    print(bk2_file)
                                    # Get replay
                                    #repvars = get_variables_from_replay(bk2_file, skip_first_step=False, inttype=retro.data.Integrations.CUSTOM_ONLY)
if __name__ == "__main__":
    args = parser.parse_args()
    main(args)