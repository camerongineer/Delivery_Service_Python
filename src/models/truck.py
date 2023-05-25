from datetime import time

__all__ = ['Truck']

from typing import Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.exceptions import TruckCapacityExceededError, PackageNotOnTruckError
from src.models.location import Location
from src.models.package import Package
from src.utilities.custom_hash import CustomHash
from src.utilities.time_conversion import TimeConversion


class Truck(CustomHash):
    hub_location = None

    def __init__(self, truck_id: int):
        super().__init__(config.NUM_TRUCK_CAPACITY)
        self._current_run = None
        self._truck_id = truck_id
        self._mileage = 0.0
        self._clock = time.min
        self._partner = None
        self._is_dispatched = False
        self._has_driver = False
        self._has_assigned_packages = False
        self._dispatch_time = None
        self._completion_time = None
        self._previous_location = None
        self._current_location = Truck.hub_location
        self._next_location = None
        self._travel_ledger = dict()
        self._pause_ledger = dict()
        self._route_runs = list()

    def __str__(self):
        return f'''
current time: {self.clock}
current location: {self.current_location.name}
remaining capacity: {self._capacity - self._size}'''

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
    def partner(self):
        return self._partner

    @property
    def is_dispatched(self):
        return self._is_dispatched

    @property
    def has_driver(self):
        return self._has_driver

    @property
    def has_assigned_packages(self):
        return self._has_assigned_packages

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

    @property
    def pause_ledger(self):
        return self._pause_ledger

    @property
    def route_runs(self):
        return self._route_runs

    @property
    def current_run(self):
        return self._current_run

    @current_run.setter
    def current_run(self, value):
        self._current_run = value

    @partner.setter
    def partner(self, value):
        if type(value) == type(self) and value is not self:
            self._partner = value
        else:
            print('Partner must another Truck')

    @dispatch_time.setter
    def dispatch_time(self, value: time):
        if not self._dispatch_time:
            self._dispatch_time = value

    @completion_time.setter
    def completion_time(self, value: time):
        self._completion_time = value

    @has_driver.setter
    def has_driver(self, value: bool):
        self._has_driver = value

    @has_assigned_packages.setter
    def has_assigned_packages(self, value: bool):
        self._has_assigned_packages = value

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
        if self._size > config.NUM_TRUCK_CAPACITY:
            raise TruckCapacityExceededError
        super().add_package(package)

    def packages(self):
        return self._arr

    def dispatch(self, current_time):
        if not self._is_dispatched:
            self._dispatch_time = current_time
            self._is_dispatched = True

    def unload(self) -> Set[Package]:
        truck_packages = set()
        for slot in self._arr:
            for package in slot:
                truck_packages.add(package)
        self._arr = [[] for _ in range(self._capacity)]
        self._size = 0
        return truck_packages

    def record(self):
        self._travel_ledger[self.mileage] = \
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

    def is_loaded(self):
        return self._size > 0

    def set_clock(self, start_time: time):
        self._clock = start_time

    def distance(self, origin_location=None, target_location=None, to_hub=False):
        if not origin_location:
            origin_location = self.current_location
        if not target_location:
            target_location = self.next_location
        if to_hub:
            target_location = self.hub_location
        if origin_location and target_location and (origin_location is not target_location):
            return origin_location.distance_dict[target_location]
        return 0

    def deliver(self):
        delivered_packages = set()
        if not self.current_location or self.current_location.is_hub:
            return delivered_packages
        for package in self.current_location.package_set:
            delivered_package = self.get_package(package.package_id)
            if not delivered_package:
                raise PackageNotOnTruckError
            package.update_status(DeliveryStatus.DELIVERED, self.clock)
            self.remove_package(package.package_id)
            delivered_packages.add(package)
        return delivered_packages

