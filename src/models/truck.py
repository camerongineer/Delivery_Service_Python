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
        self._mileage = 0.0
        self._clock = time.min
        self._has_driver = False
        self._dispatch_time = None
        self._completion_time = None
        self._previous_location = None
        self._current_location = None
        self._next_location = None
        self._travel_ledger = dict()
        self._pause_ledger = dict()

    @property
    def truck_id(self):
        return self._truck_id

    @property
    def mileage(self):
        return self._mileage

    @property
    def clock(self):
        return self._clock

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
    def current_location(self):
        return self._current_location

    @property
    def next_location(self):
        return self._next_location

    @dispatch_time.setter
    def dispatch_time(self, value: time):
        self._dispatch_time = value

    @completion_time.setter
    def completion_time(self, value: time):
        self._completion_time = value

    @property
    def pause_ledger(self):
        return self._pause_ledger

    @has_driver.setter
    def has_driver(self, value):
        if value:
            self._has_driver = True
        else:
            self._has_driver = False

    @previous_location.setter
    def previous_location(self, value: Location):
        self._previous_location = value

    @current_location.setter
    def current_location(self, value: Location):
        self._current_location = value

    @next_location.setter
    def next_location(self, value: Location):
        self._next_location = value

    def add_package(self, package: Package):
        if self._size >= config.NUM_TRUCK_CAPACITY:
            pass
            #print('Truck is at maximum capacity')
        super().add_package(package)

    def record(self):
        self._travel_ledger[self.mileage] =\
            (self.clock, self.previous_location, self.current_location, self.next_location)

    def drive(self):
        mileage_increase = 0.1
        self._mileage += mileage_increase
        time_increase = config.DELIVERY_TRUCK_MPH / 3600 / mileage_increase
        TimeConversion.increment_time(self._clock, time_increase)

    def pause(self, in_pause_start: time, in_pause_end: time):
        in_pause_start_datetime = TimeConversion.get_datetime(in_pause_start)
        in_pause_end_datetime = TimeConversion.get_datetime(in_pause_end)
        if in_pause_start_datetime >= in_pause_end_datetime:
            return
        for pause_start, pause_end in self._pause_ledger.items():
            pause_start_datetime = TimeConversion.get_datetime(pause_start)
            pause_end_datetime = TimeConversion.get_datetime(pause_end)
            if pause_start_datetime <= in_pause_start_datetime <= pause_end_datetime:
                self._pause_ledger[pause_start] = in_pause_end \
                    if in_pause_end_datetime > pause_end_datetime else pause_end
                return
            elif in_pause_start_datetime <= pause_start_datetime <= in_pause_end_datetime:
                self._pause_ledger[in_pause_start] = in_pause_end \
                    if in_pause_end_datetime > pause_end_datetime else pause_end
                del self._pause_ledger[pause_start]
                return
        self._pause_ledger[in_pause_start] = in_pause_end

    def get_mileage(self, current_time: time):
        time_difference = TimeConversion.get_seconds_between_times(self._dispatch_time, current_time)
        if time_difference == 0:
            return 0.0
        if self._completion_time:
            current_time = self._completion_time
        time_difference -= TimeConversion.get_paused_seconds(self.pause_ledger, current_time)
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

    def is_paused(self, current_time):
        for pause_start, pause_end in self._pause_ledger.items():
            if pause_start <= current_time < pause_end:
                return True
        return False

    def set_clock(self, start_time: time):
        self._clock = start_time
