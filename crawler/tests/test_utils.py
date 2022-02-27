from datetime import time

from ..utlis import Schedule
from ..utlis import parse_schedule
from ..utlis import parse_route_color
from ..utlis import parse_station_unique_id


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


def test_parse_route_color_with_no_color():
    color = parse_route_color('border-bottom: 10px solid ;')
    assert color == ''


def test_parse_route_color_with_color():
    color = parse_route_color('border-bottom: 10px solid #D88C00;')
    assert color == '#D88C00'


def test_parse_route_color_with_multiple_colors():
    color = parse_route_color(
        'border-bottom: 10px solid #3D9CD7; color: #D88C00;'
    )
    assert color == '#3D9CD7'


def test_parse_route_color_with_empty_input_string():
    color = parse_route_color('')
    assert color == ''


def test_parse_station_unique_id_example_1():
    result = parse_station_unique_id('Paradero 553A01 - Br. Cedritos')
    assert result == '553A01'


def test_parse_station_unique_id_example_2():
    result = parse_station_unique_id('Paradero TM0125 - Ciudad Universitaria')
    assert result == 'TM0125'


def test_parse_station_unique_id_example_3():
    result = parse_station_unique_id(' Paradero TM0124 - Concejo de Bogotá ')
    assert result == 'TM0124'
