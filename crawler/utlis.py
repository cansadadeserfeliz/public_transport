from typing import List
from datetime import time
from dataclasses import dataclass


@dataclass
class Schedule:
    # where Monday is 1 and Sunday is 7, 8 - public holidays
    weekdays: List[int]

    start_time: time
    end_time: time


def parse_schedule(schedule_str: str) -> Schedule:
    """Parses bus schedule string from www.transmilenio.gov.co.
    Args:
        schedule_str: a string that contains bus schedule.

        Examples:
            "L-S            | 04:00 AM            - 11:00 PM"
            "S            | 04:35 AM            - 12:20 AM"
            "D-F            | 05:00 AM            - 10:00 PM"
    Returns: a `Schedule` object.
    """

    iso_weekdays = []
    start_time = time(4, 00)
    end_time = time(23, 00)

    return Schedule(
        weekdays=iso_weekdays,
        start_time=start_time,
        end_time=end_time,
    )
