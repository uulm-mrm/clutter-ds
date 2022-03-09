#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Optional, Sequence

import h5py
import numpy as np
from radar_scenes.labels import Label as OriginalLabel
import radar_scenes.sequence

from clutter_labels import ClutterLabel


def run_script(input_strings: Optional[Sequence[str]] = None):
    """
    Execute script for automatically generating clutter annotations for the RadarScenes data set

    :param input_strings: Optional list of argument strings to parse instead of command line values. Strings must not
        contain any spaces.
    """
    # Define and read in (command line) arguments
    argparser = argparse.ArgumentParser(description="Script for automatically generating clutter annotations for the "
                                                    "RadarScenes data set.")
    argparser.add_argument("-p", "--dataset-path", type=Path, required=True,
                           help="<Required> Path of directory in which original RadarScenes data set is stored. "
                                "Absolute and relative paths are supported.\nWARNING: The original labels stored in "
                                "the directory will be overwritten by this script!")
    argparser.add_argument("-y", "--yes", action="store_true",
                           help="If this flag is set, user prompts are skipped and automatically confirmed.")
    args = argparser.parse_args(input_strings)

    # Confirm execution of label generation method
    print("Starting automatic relabeling of the RadarScenes data set for clutter detection.")
    print(f"Provided command line arguments: {vars(args)}")
    args.dataset_path = args.dataset_path.expanduser().resolve(strict=True)
    if not args.yes:
        print(f"WARNING: The original labels stored in the data set directory \"{args.dataset_path}\" are about to be "
              f"overwritten with newly generated clutter labels!")
        user_input = ""
        positive_answers = ["y", "yes"]
        negative_answers = ["n", "no"]
        while user_input not in positive_answers and user_input not in negative_answers:
            user_input = input("Are you sure you want to continue? (y/n)\n")
            if user_input.lower() in positive_answers:
                print("Continuing execution.")
            elif user_input.lower() in negative_answers:
                print("Canceling execution. No files were written to disk.")
                return
            else:
                print(f"Invalid input. Please enter one of the following: {positive_answers + negative_answers}.")

    # Execute label generation method
    generate_clutter_labels(args.dataset_path)


def generate_clutter_labels(dataset_path: Path):
    """
    Generate new ground-truth regarding the occurrence of clutter for the RadarScenes data set and store it to disk.
    Note that the original annotations are overwritten in the process. The three new classes that are distinguished are
    *moving object*, *stationary* and *clutter*.

    :param dataset_path: Absolute path of directory in which RadarScenes data set, whose original annotations should be
        replaced by clutter labels, is stored
    """
    print("THIS METHOD IS ONLY A DUMMY AND DOES NOT CONTAIN ANY FUNCTIONALITY! THE ACTUAL LABEL GENERATION CODE WILL BE "
          "PROVIDED WHEN THE CORRESPONDING PAPER IS ACCEPTED.")


if __name__ == '__main__':
    run_script()
