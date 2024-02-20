import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument(
    "-d",
    "--datapath",
    default='.',
    type=str,
    help="Data path to look for events.tsv and .bk2 files. Should be the root of the mario dataset.",
)


def main(args):
    # Get datapath
    DATA_PATH = args.datapath
    if DATA_PATH == ".":
        print("No data path specified. Searching files in this folder.")
    print('Generating annotations for the mario dataset in : {DATA_PATH}')


if __name__ == "__main__":

    args = parser.parse_args()
    main(args)