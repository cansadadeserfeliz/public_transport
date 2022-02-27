import re
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


def parse_route_color(route_style_str: str) -> str:
    """
    Args:
        route_style_str: a string that CSS styles for a route.

        Examples:
            border-bottom: 10px solid ;
            border-bottom: 10px solid #3D9CD7;
            border-bottom: 10px solid #D88C00;
    """
    match = re.search(r'#(?:[0-9a-fA-Z]{3}){1,2}', route_style_str)
    if match:
        return match.group()
    return ''


def parse_station_unique_id(station_title_str: str) -> str:
    match = re.search(r'Paradero\s(?P<code>[0-9A-Z]{6})\s', station_title_str)
    if match:
        return match.group('code')
    return ''
