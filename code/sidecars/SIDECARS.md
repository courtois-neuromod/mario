# Repetition-level gameplay data
To make gameplay data easily accessible, we provide a set of sidecar files for each ­´*.bk2´ file recorded. These sidecars contain information about frames, RAM states or global metrics for a single repetition. A set of 4 different sidecars is created for each replay : a global info sidecar, a movie sidecar, a framewise info sidecar and a framewise info dict.

## Global info
The global info sidecar contains general informations about a repetition (e.g. Was this repetition succesfully completed by the player ? How many coins/powerups did the player collect ? How many enemies were killed during this repetition ? What was the final player score ?). It is stored as a JSON file, and has the same filename as its source BK2 file.

## Framewise info
The framewise info file is created by stable-retro's replay function. It is stored as a .npz file, that contains two objects : the game variables data, and the actions data. It is fully compatible with the stable-retro framework.

## Framewise dict
The framewise dict contains the same informations as the framewise info sidecar, but these are reformated to populate a dictionnary. Each key of this dictionnary is a game variable, and contains a list of values for that variable at each frame of the replay. This file was created to facilitate access to game variables outside of the stable-retro framework.

## Movie
The movie sidecar is a video replay (with audio) of the BK2 file­.
