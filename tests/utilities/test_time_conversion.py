from datetime import time
from unittest import TestCase

from src import config
from src.utilities.time_conversion import TimeConversion


class TestTimeConversion(TestCase):
    def test_convert_time_difference_to_miles(self):
        start_time = time(hour=8)
        end_time = time(hour=9)
        assert TimeConversion.convert_time_difference_to_miles(start_time, end_time) == config.DELIVERY_TRUCK_MPH
        assert TimeConversion.convert_time_difference_to_miles(end_time, start_time) == 0.0
        end_time = time(hour=10)
        assert TimeConversion.convert_time_difference_to_miles(start_time, end_time) == config.DELIVERY_TRUCK_MPH * 2

    def test_convert_miles_to_time(self):
        miles = config.DELIVERY_TRUCK_MPH
        start_time = time(hour=8)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) == time(hour=9)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) != time(hour=9, minute=1)
        miles = config.DELIVERY_TRUCK_MPH * 2
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) != time(hour=9)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) == time(hour=10)

    def test_get_paused_seconds(self):
        pause_ledger = dict()
        current_time = time(hour=10)
        assert TimeConversion.get_paused_seconds(pause_ledger, current_time) == 0
        pause_ledger[time(hour=9)] = time(hour=9, minute=30)
        assert TimeConversion.get_paused_seconds(pause_ledger, current_time) == 60 * 30
        pause_ledger[time(hour=10)] = time(hour=10, minute=30)
        assert TimeConversion.get_paused_seconds(pause_ledger, current_time) == 60 * 30
        current_time = time(hour=10, minute=15)
        assert TimeConversion.get_paused_seconds(pause_ledger, current_time) == 60 * 45
        current_time = time(hour=10, minute=30)
        assert TimeConversion.get_paused_seconds(pause_ledger, current_time) == 60 * 60

    def test_add_time_delta(self):
        current_time = time(hour=9)
        delta_seconds = 1800
        new_time = TimeConversion.add_time_delta(current_time, delta_seconds)
        assert current_time != new_time
        assert new_time == time(hour=9, minute=30)
        delta_seconds = -1800
        new_time = TimeConversion.add_time_delta(new_time, delta_seconds)
        assert current_time == new_time
