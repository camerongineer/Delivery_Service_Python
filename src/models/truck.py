from datetime import time




__all__ = ['Truck']

from src import config
from src.models.location import Location
from src.models.package import Package
from src.utilities.custom_hash import CustomHash
from src.utilities.time_conversion import TimeConversion


class Truck(CustomHash):
    hub_location = None

    def __init__(self, truck_id: int):
        super().__init__(config.NUM_TRUCK_CAPACITY)
        self._truck_id = truck_id
        self._has_driver = False
        self._dispatch_time = None
        self._completion_time = None
        self._previous_location = None
        self._next_location = None
        self._travel_ledger = dict()
        self._pause_ledger = dict()

    @property
    def truck_id(self):
        return self._truck_id

    @property
    def has_driver(self):
        return self._has_driver

    @property
    def dispatch_time(self):
        return self._dispatch_time

    @property
    def completion_time(self):
        return self._completion_time

    @property
    def previous_location(self):
        return self._previous_location

    @property
    def next_location(self):
        return self._next_location

    @dispatch_time.setter
    def dispatch_time(self, value: time):
        self._dispatch_time = value

    @completion_time.setter
    def completion_time(self, value: time):
        self._completion_time = value

    @has_driver.setter
    def has_driver(self, value):
        if value:
            self._has_driver = True
        else:
            self._has_driver = False

    @previous_location.setter
    def previous_location(self, value: Location):
        self._previous_location = value

    @next_location.setter
    def next_location(self, value: Location):
        self._next_location = value

    def add_package(self, package: Package):
        if self._size >= config.NUM_TRUCK_CAPACITY:
            pass
            #print('Truck is at maximum capacity')
        super().add_package(package)

    def set_travel_ledger(self, travel_ledger: dict):
        self._travel_ledger = travel_ledger

    def pause(self, pause_start: time, pause_end: time):
        self._pause_ledger[pause_start] = pause_end

    def get_mileage(self, current_time: time):
        time_difference = TimeConversion.get_seconds_between_times(self._dispatch_time, current_time)
        if time_difference == 0:
            return 0.0
        if self._completion_time:
            current_time = self._completion_time
        time_difference -= self._total_paused_seconds(current_time)
        miles_per_second = config.DELIVERY_TRUCK_MPH / 3600
        return time_difference * miles_per_second

    def get_current_location(self, current_time: time):
        mileage = self.get_mileage(current_time)
        sorted_stop_miles = sorted(self._travel_ledger.keys(), key=lambda location_mileage: float(location_mileage))
        for i in range(len(sorted_stop_miles) - 1):
            if mileage == sorted_stop_miles[i]:
                return self._travel_ledger[i][0]
            elif sorted_stop_miles[i] < mileage < sorted_stop_miles[i + 1]:
                return self._travel_ledger[sorted_stop_miles[i]]
        return None

    def _total_paused_seconds(self, current_time: time) -> int:
        total_paused_seconds = 0
        for pause_start_time, pause_end_time in self._pause_ledger.items():
            if pause_start_time < current_time:
                time_to_compare = pause_end_time if pause_end_time < current_time else current_time
                total_paused_seconds += TimeConversion.get_seconds_between_times(pause_start_time, time_to_compare)
        return total_paused_seconds

    def is_paused(self, current_time):
        for pause_start, pause_end in self._pause_ledger.items():
            if pause_start <= current_time < pause_end:
                return True
        return False
