from datetime import time

from ..utlis import Schedule
from ..utlis import parse_schedule


def test_parse_saturday_schedule():
    schedule = parse_schedule('S            | 04:35 AM            - 12:20 AM')
    assert isinstance(schedule, Schedule)
    assert schedule.weekdays == [6]
    assert schedule.start_time == time(4, 35)
    assert schedule.end_time == time(0, 20)


def test_parse_monday_to_saturday_schedule():
    schedule = parse_schedule(
        'L-S            | 04:00 AM            - 11:00 PM'
    )
    assert isinstance(schedule, Schedule)
    assert schedule.weekdays == [1, 2, 3, 4, 5, 6]
    assert schedule.start_time == time(4, 00)
    assert schedule.end_time == time(23, 00)


def test_parse_sunday_schedule():
    schedule = parse_schedule(
        'D-F            | 05:00 AM            - 10:00 PM'
    )
    assert isinstance(schedule, Schedule)
    assert schedule.weekdays == [7]
    assert schedule.start_time == time(5, 00)
    assert schedule.end_time == time(22, 00)
