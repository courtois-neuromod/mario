# Gameplay annotations for the mario dataset
In order to benefit from the complex structure of the mario task, a number of variables are extracted from the replays obtained during data acquisitions. The produced annotations are encoded in a BIDS-compatible format, i.e. a .tsv file with at least 3 rows : onset, duration and event_type (sometimes named trial_type). The ­­­­´*desc-annotated­­´ files outputed by this script contains two main types of annotations : action annotations, and events annotations.

## Events file structure
The annotated_events.tsv files contain the classical BIDS events fields : trial_type, onset and duration. Several other fields were added to help relate these annotations to the .bk2 frames at which they were detected, and to provide information about the SMB level associated with the recording.

- trial_type : Name of the event
- onset : Onset of the event, in seconds, relative to the beginning of the run
- duration : Duration of the event, in seconds, relative to the onset
- level : Level of SMB in which the current repetition was played
- rep_index : Index of the repetition, relative to the beginning of the run (only for repetition events)
- stim_file : Path to the .bk2 file related to a repetition (only for repetition events)
- frame_start : Frame ID of the event onset, in frames, relative to the first frame of the current repetition
- frame_stop : Frame ID of the event offset, in frames, relative to the first frame of the current repetition


## Action annotations
Action annotations exhaustively describe the player's inputs throughout the game. Their onset reflect the timing of the keypress, relative to the beginning of the run, and the duration corresponds to the time elapsed between the key press and the key release. 
The available actions for this dataset are : 
- A : Jump
- B : Run/fireball throw
- LEFT : Player moves left
- RIGHT : Player moves right
- UP : Climb up
- DOWN : Crouch/Climb down

## Events annotations
In addition to the action annotations, we also encoded events extracted from the RAM of the game replays. These events are conditionned by player actions but also by the current gamestate. In the annotation file, these events have been attributed a duration of 0, although the duration of the corresponding animations on screen might vary. These events include : 
- Kill/stomp : Mario kills an enemy by landing on its head
- Kill/impact : Mario kills an enemy by bumping a brick under the enemy or by running through it in invincibility
- Kill/kick : Mario kills an enemy by kicking a shell and hitting them with it
- Hit/powerup_lost : Mario gets hit and loses a powerup
- Hit/life_lost : Mario gets hit and loses a life
- Brick_smashed : Mario smashes a brick
- Coin_collected : Mario collects a coin
- Powerup_collected : Mario collects a powerup

## Scenes annotations
To guide behavioral analysis of SMB gameplay, we splitted the levels into "scenes", which correspond to segments of roughly one screen length, determined by the player position in the level. Each scene can be conceived as a "problem" posed to the player, composed of various design patterns. The scenes annotations in the annotated_events.tsv file correspond to the moment a player enters a scene, and lasts until the player exits the scene. Scene events are identified by the value "scene-{sceneID}" in the "trial_type" column. The scene ID is composed as followed : w{world}l{level}s{sceneNumber}. For example, w1l1s1 is the scene number 1 of World 1 Level 1.

TODO : explain scene codes
