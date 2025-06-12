
import pathlib, bids.layout,pandas as pd, os, shutil, re
sourcedata=pathlib.Path('/unf/eyetracker/neuromod/mario/sourcedata')
bids_path=pathlib.Path('.')
bids_layout=bids.BIDSLayout(bids_path, database_path=bids_path / '.pybids_cache')


for ses_path in sorted(sourcedata.glob('sub-0[1-6]/ses-0[0-9][0-9]')):
    event_fnames = ses_path.glob('*_task-mario_*_events.tsv')
    dfs = {evf:pd.read_csv(evf, delimiter='\t') for evf in event_fnames}
    dfs_complete = {evf:df for evf,df in dfs.items() if any(df.trial_type=='questionnaire-answer') and sum(df.trial_type=='gym-retro_game') > 2}
    if not len(dfs_complete):
        print(ses_path, 'no complete event files')
        continue                                            
    ses_ents = bids.layout.parse_file_entities(next(iter(dfs_complete.keys())))                                                                         
    ses_ents['session'] = f"{int(ses_ents['session']):03d}" #fix zero-padding mistake                                     
    ses_evt_files = bids_layout.get(**{k:ses_ents[k] for k in ['subject', 'session', 'task','suffix']})
    mismatch = len(dfs_complete) != len(ses_evt_files)
    print(ses_path, len(dfs_complete), len(ses_evt_files), 'mismatch' if mismatch else '')                                                

    targets_found = True                                                              
    targets = {}
    runs = []
    for evf in sorted(dfs_complete.keys()):                                           
        bids_ents = bids.layout.parse_file_entities(evf)
        if bids_ents['run'] in runs:
            bids_ents['run'] = max(runs)+1
            print(f"{evf} run is duplicated  ______ taking max(runs)+1 = {bids_ents['run']}")
        bids_ents['session'] = f"{int(bids_ents['session']):03d}" #fix zero-padding mistakes                                                           
        target_evt = bids_layout.get(**bids_ents)                                                         
        if len(target_evt) != 1:                                                                          
            print(f"{evf} not matched ####### action needed")                         
            targets_found=False                                                       
            break
        elif target_evt[0].path in targets.values():
            print(f"{evf} is duplicated ####### action needed")
            targets_found=False
        else:
            targets[evf] = target_evt[0].path
        runs.append(bids_ents['run'])

    all_new_dfs = []
    for evf in sorted(dfs_complete.keys()):
                                                                      
        old_df = dfs[evf]  
        quest_lines = old_df.trial_type!='gym-retro_game'
        old_df.stim_file.loc[quest_lines]='n/a' # questionnaire is not level specific
        old_df.level.loc[quest_lines]='n/a' # questionnaire is not level specific
       
        df=old_df.copy()
        df['stim_file'] = df['stim_file'].str.replace(
            '/scratch/neuromod/data/mario/sourcedata/','').str.replace('/sub-','/gamelogs/sub-')
        df['stim_file'] = df['stim_file'].str.replace(
            r'[0-9]{8}-[0-9]{6}_[^_]+_Level([0-9])-([0-9])_([0-9]{3})',
            lambda m: f"task-mario_level-w{m.group(1)}l{m.group(2)}_rep-{m.group(3)}",
            regex=True)

        target_evt = targets.get(evf, f"sub-{ses_ents['subject']}/ses-{ses_ents['session']}/func/{os.path.basename(evf)}")
        print(f"saving {target_evt}")

        for ri, row in df.iterrows():
            if row.trial_type == 'gym-retro_game':
                inc=0
                while any([d.stim_file.eq(df.stim_file[ri]).any() for d in all_new_dfs + [df[:ri]]]):
                    inc += 1
                    df.stim_file[ri] = re.sub(r'rep-([0-9]{3})', lambda m: f"rep-{int(m.groups()[0]) + inc:03d}", row.stim_file)
                    print(f'replace {df.stim_file[ri]}')
        all_new_dfs.append(df)
        
        if not os.path.exists(os.path.dirname(target_evt)):
            print('session not converted/merged')
            continue
        df.to_csv(target_evt, sep='\t')
        
        for row_old, row_new in zip(old_df.iterrows(), df.iterrows()):                               
           if row_new[1].trial_type=='gym-retro_game':
               os.makedirs(os.path.dirname(row_new[1].stim_file), exist_ok=True)
               shutil.copyfile(
                   row_old[1].stim_file.replace('/scratch/neuromod/data/mario/sourcedata', sourcedata.as_posix()),
                   row_new[1].stim_file)
               print(row_new[1].stim_file)
