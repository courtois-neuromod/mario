# Gameplay annotations for the mario dataset
In order to benefit from the complex structure of the mario task, a number of variables are extracted from the replays obtained during data acquisitions. The produced annotations are encoded in a BIDS-compatible format, i.e. a .tsv file with at least 3 rows : onset, duration and event_type (sometimes named trial_type). The ­­­­´*desc-annotated­­´ files outputed by this script contains two main types of annotations : action annotations, and events annotations.

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
