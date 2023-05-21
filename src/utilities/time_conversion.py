from datetime import datetime, time, timedelta

from src import config


# def _get_seconds_since_midnight(in_time: time) -> float:
#     in_datetime = TimeConversion.get_datetime(in_time)
#     midnight = TimeConversion.get_datetime(time.min)
#     return (in_datetime - midnight).total_seconds()


class TimeConversion:
    @staticmethod
    def convert_time_difference_to_miles(start_time: time, end_time: time, miles_per_hour=config.DELIVERY_TRUCK_MPH) -> float:
        time_difference = TimeConversion.get_seconds_between_times(start_time, end_time)
        miles_per_second = miles_per_hour / 3600
        return time_difference * miles_per_second

    @staticmethod
    def convert_miles_to_time(miles: float, start_time: time, pause_seconds=0,
                              miles_per_hour=config.DELIVERY_TRUCK_MPH) -> time:
        if miles <= 0:
            return start_time
        time_seconds = ((miles / miles_per_hour) * 3600) + pause_seconds
        return TimeConversion.add_time_delta(start_time, time_seconds)

    @staticmethod
    def get_datetime(in_time: time) -> datetime:
        return datetime.combine(config.DELIVERY_DATE, in_time)

    @staticmethod
    def increment_time(in_time: time, time_seconds=1):
        in_datetime = TimeConversion.get_datetime(in_time)
        in_datetime = in_datetime + timedelta(seconds=time_seconds)
        return in_datetime.time()

    @staticmethod
    def get_seconds_between_times(start_time: time, end_time: time) -> int:
        start_datetime = TimeConversion.get_datetime(start_time)
        end_datetime = TimeConversion.get_datetime(end_time)
        return (end_datetime - start_datetime).seconds if start_time < end_time else 0

    @staticmethod
    def is_time_at_or_before_other_time(origin_time: time, other_time: time) -> bool:
        return TimeConversion.get_datetime(origin_time) <= TimeConversion.get_datetime(other_time)

    @staticmethod
    def get_paused_seconds(truck_pause_ledger: dict, current_time: time):
        total_paused_seconds = 0
        for pause_start_time, pause_end_time in truck_pause_ledger.items():
            if pause_start_time < current_time:
                time_to_compare = pause_end_time if pause_end_time < current_time else current_time
                total_paused_seconds += TimeConversion.get_seconds_between_times(pause_start_time, time_to_compare)
        return total_paused_seconds

    @staticmethod
    def add_time_delta(start_time: time, time_seconds: int):
        return (TimeConversion.get_datetime(start_time) + timedelta(seconds=time_seconds)).time()

