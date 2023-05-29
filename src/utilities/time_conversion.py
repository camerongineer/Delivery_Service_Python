from datetime import datetime, time, timedelta

from src import config


class TimeConversion:
    """
    Provides utility methods for time conversions and calculations.
    """

    @staticmethod
    def convert_time_difference_to_miles(origin_time: time, target_time: time,
                                         miles_per_hour=config.DELIVERY_TRUCK_MPH) -> float:
        """
        Converts the time difference between two given times to miles traveled based on the average speed.

        Args:
            origin_time (time): The origin time.
            target_time (time): The target time.
            miles_per_hour (float, optional): The average speed in miles per hour. Defaults to config.DELIVERY_TRUCK_MPH.

        Returns:
            float: The calculated distance in miles.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        time_difference = TimeConversion.get_seconds_between_times(origin_time, target_time)
        miles_per_second = miles_per_hour / 3600
        return time_difference * miles_per_second

    @staticmethod
    def convert_miles_to_time(miles: float, origin_time: time, pause_seconds=0,
                              miles_per_hour=config.DELIVERY_TRUCK_MPH) -> time:
        """
        Converts the given distance in miles to the corresponding time based on the average speed.

        Args:
            miles (float): The distance in miles.
            origin_time (time): The origin time.
            pause_seconds (int, optional): Additional pause time in seconds. Defaults to 0.
            miles_per_hour (float, optional): The average speed in miles per hour. Defaults to config.DELIVERY_TRUCK_MPH.

        Returns:
            time: The calculated time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if miles <= 0:
            return origin_time
        time_seconds = ((miles / miles_per_hour) * 3600) + pause_seconds
        return TimeConversion.add_time_delta(origin_time, time_seconds)

    @staticmethod
    def get_datetime(origin_time: time) -> datetime:
        """
        Converts the given time to a datetime object with the default delivery date.

        Args:
            origin_time (time): The origin time.

        Returns:
            datetime: The converted datetime object.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return datetime.combine(config.DELIVERY_DATE, origin_time)

    @staticmethod
    def increment_time(origin_time: time, time_seconds=1) -> time:
        """
        Increments the given time by the specified number of seconds.

        Args:
            origin_time (time): The origin time.
            time_seconds (int, optional): The number of seconds to increment. Defaults to 1.

        Returns:
            time: The incremented time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        in_datetime = TimeConversion.get_datetime(origin_time)
        in_datetime = in_datetime + timedelta(seconds=time_seconds)
        return in_datetime.time()

    @staticmethod
    def get_seconds_between_times(origin_time: time, target_time: time) -> int:
        """
        Calculates the number of seconds between two given times.

        Args:
            origin_time (time): The origin time.
            target_time (time): The target time.

        Returns:
            int: The number of seconds between the times.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        start_datetime = TimeConversion.get_datetime(origin_time)
        end_datetime = TimeConversion.get_datetime(target_time)
        return (end_datetime - start_datetime).seconds if origin_time < target_time else 0

    @staticmethod
    def is_time_at_or_before_other_time(origin_time: time, other_time: time) -> bool:
        """
        Checks if one time is at or before another time.

        Args:
            origin_time (time): The origin time.
            other_time (time): The other time.

        Returns:
            bool: True if the origin time is at or before the other time, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return TimeConversion.get_datetime(origin_time) <= TimeConversion.get_datetime(other_time)

    @staticmethod
    def add_time_delta(origin_time: time, time_seconds: int) -> time:
        """
        Adds a specified number of seconds to a given time and returns the resulting time.

        Args:
            origin_time (time): The origin time.
            time_seconds (int): The number of seconds to add.

        Returns:
            time: The resulting time after adding the seconds.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return (TimeConversion.get_datetime(origin_time) + timedelta(seconds=time_seconds)).time()

    @staticmethod
    def seconds_between_times(origin_time: time, target_time: time) -> float:
        """
        Calculates the number of seconds between two given times.

        Args:
            origin_time (time): The origin time.
            target_time (time): The target time.

        Returns:
            float: The number of seconds between the times.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        time_difference = TimeConversion.get_datetime(target_time) - TimeConversion.get_datetime(origin_time)
        seconds = time_difference.total_seconds()
        return seconds
