import pandas as pd
import pathlib
#import bids.layout
import pytest_check as check
import glob
import json
import zipfile
import numpy as np
import os

RUN_DURATION_THRESHOLD = 10
FRAME_RATE = 60.099826520671044 #frame rate given by retro emulator.em.get_screen_rate()

def test_events_duration():
    bids_path = pathlib.Path('.')
#    bids_layout = bids.BIDSLayout(bids_path, database_path=bids_path / '.pybids_cache')
#
#    all_bolds = bids_layout.get(suffix='bold', extension='nii.gz', part='mag')
    all_events = sorted(glob.glob('sub-*/ses-*/func/*task-mario*_events.tsv'))


    for evt_file in all_events:
        events = pd.read_csv(evt_file, sep='\t')
        last_evt_end = float(events.onset.take([-1]) + (events.duration.take([-1]) if 'duration' in events.keys() else 0))
        first_evt_quest = float(events.onset[events.trial_type=='questionnaire-value-change'].take([1]))
        
        bold_json = evt_file.rstrip('_events.tsv') + '_part-mag_bold.json'
        if not os.path.exists(bold_json):
            print(f"{evt_file} do not match a bold file")
            continue
        with open(bold_json, 'r') as fd:
            bold_md = json.load(fd)
        n_trs = int(bold_md['dcmmeta_shape'][-1])
        tr = float(bold_md['RepetitionTime'])
        run_duration = n_trs * tr

        print(run_duration, last_evt_end, evt_file)
        # if stopped during last TR, it is discarded by the scanner, so we check it's -1 TR long
        #check.greater(run_duration + tr, last_evt_end, f"bold run is shorter than event file: {bold_json} {run_duration} < {last_evt_end}")
        check.greater(run_duration + tr, first_evt_quest, f"bold run is shorter than questionnaire: {bold_json} {run_duration} < {last_evt_end}")
        #check.less(run_duration, last_evt_end + RUN_DURATION_THRESHOLD, f"bold run is suspiciously longer than event file {bold_json}")
        

        events['duration'] = 0
        events = events[events.trial_type=='gym-retro_game']
        for ri, row in events.iterrows():
            bk2 = row.stim_file
            bk2zip = zipfile.ZipFile(bk2, 'r')
            inputlog = bk2zip.read('Input Log.txt').decode('utf-8').split('\n')
            n_kpress = len(inputlog)-3 # 3 lines of header/footer
            events.loc[ri,'duration'] = n_kpress/FRAME_RATE
        intervals = np.asarray(events.onset)[1:] - (np.asarray(events.onset)[:-1] + np.asarray(events.duration)[:-1])
        if any(np.abs(intervals-6) > 1):
            print(f"${evt_file} intervals are weird")
            print(f"{intervals}")
            print(np.asarray(events.onset)[1:])
            print(np.asarray(events.onset)[:-1] + np.asarray(events.duration)[:-1])

            print(events[1:].stim_file[np.abs(intervals-6) > 1])
        
            

