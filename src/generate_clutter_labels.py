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
        replaced with clutter labels, is stored
    """
    dataset_path = dataset_path.joinpath("data")

    # Iterate over all sequences in data set
    sequences = radar_scenes.sequence.read_sequences_json(str(dataset_path.joinpath("sequences.json")))["sequences"]
    for seq_name in sequences.keys():
        print(f"Starting label generation for sequence \"{seq_name}\".")
        seq_dir = dataset_path.joinpath(seq_name)
        seq_data = radar_scenes.sequence.Sequence.from_json(str(seq_dir.joinpath("scenes.json")))

        seq_radar_data_file_path = seq_dir.joinpath("radar_data.h5")
        with h5py.File(str(seq_radar_data_file_path), 'r+') as seq_radar_data_file:
            # Iterate over all scenes (i.e. scans) in sequence
            for scene_info in seq_data._scenes.values():
                scene_radar_data = seq_radar_data_file["radar_data"][scene_info["radar_indices"][0]:
                                                                     scene_info["radar_indices"][1]]

                # Iterate over all detection points in scene and derive their new labels
                relabeled_scene_radar_data = scene_radar_data.copy()
                for detection, relabeled_detection in zip(scene_radar_data, relabeled_scene_radar_data):
                    if detection[-1] != OriginalLabel.STATIC.value:  # original label = any object class
                        # Mark detection as moving object
                        relabeled_detection[-1] = ClutterLabel.MOVING_OBJECT.value

                        # Search for moving background detections in close proximity to current object detection and
                        # assign them to object class as well. This introduces tolerances for ordinary measurement
                        # errors, so that detections do not have to lie perfectly inside an object's bounding box to be
                        # labeled as such.

                        # Set maximum tolerated distance error to 0.3m
                        max_distance_error = 0.3  # in m
                        # Set maximum tolerated azimuth error for a detection seen at current angle. Allow 2° error at
                        # 0° angle and increase linearly to 4° error at 60° angle and above.
                        max_azimuth_error = np.pi / 90 + min(abs(detection[3]), np.pi / 3) * 1 / 30  # in rad

                        for relabeled_detection_2 in relabeled_scene_radar_data:
                            if is_detection_moving(relabeled_detection_2) and \
                                    (detection[2] - max_distance_error <= relabeled_detection_2[2] <=
                                     detection[2] + max_distance_error) and \
                                    (detection[3] - max_azimuth_error <= relabeled_detection_2[3] <=
                                     detection[3] + max_azimuth_error):
                                # Label detection as moving object
                                relabeled_detection_2[-1] = ClutterLabel.MOVING_OBJECT.value

                    else:  # original label = static (i.e. background)
                        # Check if detection has already been assigned to a new class (due to proximity to an object
                        # detection)
                        if relabeled_detection[-1] != OriginalLabel.STATIC.value:
                            continue

                        # Label detections with ego motion compensated velocity above threshold as clutter, the others
                        # as stationary
                        if is_detection_moving(detection):
                            relabeled_detection[-1] = ClutterLabel.CLUTTER.value
                        else:
                            relabeled_detection[-1] = ClutterLabel.STATIONARY.value

                # Store newly generated labels for current scene to disk
                seq_radar_data_file["radar_data"][scene_info["radar_indices"][0]:scene_info["radar_indices"][1]] = \
                    relabeled_scene_radar_data

    print("Success! Original labels of RadarScenes data set were replaced with newly generated annotations regarding "
          "clutter.")


def is_detection_moving(detection: np.void) -> bool:
    """
    Check whether a detection is moving, i.e. whether it is certain not to represent a stationary object (which is the
    case if its ego motion compensated velocity is above a certain threshold)

    :param detection: np-data-tuple representing a detection in format defined by RadarScenes data set
    :return: True if detection is moving, otherwise False
    """
    # Set velocity threshold to 3x the standard deviation of the sensor's velocity measurement (= 3*0.1m/s) plus an
    # estimate of the maximum error introduced during ego motion compensation (= 0.2m/s)
    velocity_threshold_moving = 0.5  # in m/s

    # For scenes in which the ego vehicle is standing still, the ego motion compensated velocity is sometimes missing
    # from the data. But in that case, the relative velocity (which is always available) corresponds to ego motion
    # compensated one and can thus be used instead.
    return (not np.isnan(detection[6]) and abs(detection[6]) >= velocity_threshold_moving) or \
        (np.isnan(detection[6]) and abs(detection[5]) >= velocity_threshold_moving)


if __name__ == '__main__':
    run_script()
