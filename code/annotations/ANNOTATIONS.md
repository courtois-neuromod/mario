# Gameplay annotations for the mario dataset
In order to benefit from the complex structure of the mario task, a number of variables are extracted from the replays obtained during data acquisitions. The produced annotations are encoded in a BIDS-compatible format, i.e. a .tsv file with at least 3 rows : onset, duration and event_type (sometimes named trial_type). These files encode the beginning and start of each repetition, but also contains the values of state variables as well as some handcrafted annotations.

