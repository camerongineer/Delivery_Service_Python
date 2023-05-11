from datetime import time
from unittest import TestCase

from src.utilities.time_conversion import TimeConversion


class TestTimeConversion(TestCase):
    def test_convert_time_difference_to_miles(self):
        start_time = time(hour=8)
        end_time = time(hour=9)
        assert TimeConversion.convert_time_difference_to_miles(start_time, end_time) == 18.0
        assert TimeConversion.convert_time_difference_to_miles(end_time, start_time) == 0.0
        assert TimeConversion.convert_time_difference_to_miles(start_time, end_time) != 18.1

    def test_convert_miles_to_time(self):
        miles = 18.0
        start_time = time(hour=8)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) == time(hour=9)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) != time(hour=9, minute=1)
        miles = 36.0
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) != time(hour=9)
        assert TimeConversion.convert_miles_to_time(miles, start_time, 0) == time(hour=10)
