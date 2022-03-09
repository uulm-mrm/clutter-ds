#!/usr/bin/env python3
from enum import Enum


class ClutterLabel(Enum):
    """
    Label enum of clutter labels for radar clutter data set
    """
    CLUTTER = 0
    MOVING_OBJECT = 1
    STATIONARY = 2

    @staticmethod
    def label_id_to_name(label_id: int) -> str:
        """
        Convert integer label ID to string representation

        :param label_id: Label ID of class for which string is desired
        :return: Class name as string
        """
        return ClutterLabel(label_id).name
