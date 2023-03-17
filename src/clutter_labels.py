#!/usr/bin/env python3
from enum import Enum, unique


@unqiue
class ClutterLabel(Enum):
    """
    Label enum of clutter labels for radar clutter data set
    """
    CLUTTER = 0
    MOVING_OBJECT = 1
    STATIONARY = 2

    @staticmethod
    def class_idx_to_name(class_idx: int) -> str:
        """
        Convert integer class index to string of class name

        :param class_idx: Index of class for which string is desired
        :return: Class name as string
        """
        return ClutterLabel(class_idx).name
