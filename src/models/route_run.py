from datetime import time
from typing import Set, List

from src import config
from src.constants.run_focus import RunFocus
from src.exceptions.route_builder_error import InvalidRouteRunError
from src.models.location import Location
from src.models.package import Package
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion


class RouteRun:

    def __init__(self, return_to_hub: bool = False, start_time: time = config.DELIVERY_DISPATCH_TIME):
        self._target_location = None
        self._start_time: time = start_time
        self._estimated_completion_time = None
        self._requirements_met = None
        self._estimated_mileage: float = 0
        self._ordered_route: List[Location] = []
        self._required_packages: Set[Package] = set()
        self._locations: Set[Location] = set()
        self._assigned_truck_id = None
        self._return_to_hub: bool = return_to_hub
        self._focused_run = None
        self._run_analysis_dict = None
        self._error_location = None
        self._error_type = None


    @property
    def ordered_route(self):
        return self._ordered_route

    @property
    def required_packages(self):
        return self._required_packages

    @property
    def requirements_met(self):
        return self._requirements_met

    @property
    def return_to_hub(self):
        return self._return_to_hub

    @property
    def locations(self):
        return self._locations

    @property
    def estimated_mileage(self):
        return self._estimated_mileage

    @property
    def estimated_completion_time(self):
        return self._estimated_completion_time

    @property
    def start_time(self):
        return self._start_time

    @property
    def target_location(self):
        return self._target_location

    @property
    def assigned_truck_id(self):
        return self._assigned_truck_id

    @property
    def focused_run(self):
        return self._focused_run

    @property
    def run_analysis_dict(self):
        return self._run_analysis_dict

    @property
    def error_location(self):
        return self._error_location

    @error_location.setter
    def error_location(self, value: Location):
        self._error_location = value

    @ordered_route.setter
    def ordered_route(self, value: Set[Location]):
        self._ordered_route = value

    @requirements_met.setter
    def requirements_met(self, value: bool):
        self._requirements_met = value

    @locations.setter
    def locations(self, value: Set[Location]):
        self._locations = value

    @target_location.setter
    def target_location(self, value: Location):
        self._target_location = value

    @assigned_truck_id.setter
    def assigned_truck_id(self, value: int):
        self._assigned_truck_id = value

    @start_time.setter
    def start_time(self, value: time):
        self._start_time = value

    @focused_run.setter
    def focused_run(self, value: RunFocus):
        self._focused_run = value

    @required_packages.setter
    def required_packages(self, value):
        self._required_packages = value

    @run_analysis_dict.setter
    def run_analysis_dict(self, value: dict):
        self._run_analysis_dict = value

    @property
    def error_type(self):
        return self._error_type

    @error_type.setter
    def error_type(self, value):
        self._error_type = value

    def package_total(self, alternate_locations: Set[Location] = None):
        return len(self.get_all_packages(alternate_locations))

    def set_estimated_mileage(self):
        self._estimated_mileage = self.get_estimated_mileage_at_location(index=len(self.ordered_route) - 1)

    def set_estimated_completion_time(self):
        self._estimated_completion_time = TimeConversion.convert_miles_to_time(self._estimated_mileage,
                                                                               self._start_time, pause_seconds=0)

    def set_assigned_truck_id(self):
        for location in self.ordered_route:
            if location.is_hub:
                continue
            for package in location.package_set:
                if package.assigned_truck_id and not self.assigned_truck_id:
                    self.assigned_truck_id = package.assigned_truck_id
                elif (package.assigned_truck_id and self.assigned_truck_id and
                      package.assigned_truck_id != self.assigned_truck_id):
                    raise InvalidRouteRunError

    def set_required_packages(self):
        for location in self.locations:
            if location.is_hub:
                continue
            self.required_packages.update(location.package_set)
        for package in PackageHandler.get_bundled_packages(ignore_assigned=False):
            if package in self.required_packages:
                self.required_packages.update(PackageHandler.get_bundled_packages(ignore_assigned=True))

    def get_all_packages(self, alternate_locations: Set[Location] = None):
        all_packages = set()
        for location in (alternate_locations if alternate_locations else self.locations):
            if location.is_hub:
                continue
            all_packages.update(location.package_set)
        return all_packages

    def get_estimated_mileage_at_location(self, target_location: Location = None, index: int = None):
        mileage = 0
        if index == 0:
            return 0
        length_of_route = len(self.ordered_route) - 1 if not index else index
        i = 1
        while i <= length_of_route:
            previous_location = self.ordered_route[i - 1]
            next_location = self.ordered_route[i]
            miles_to_next = previous_location.distance(next_location)
            if previous_location is target_location:
                return mileage
            else:
                mileage += miles_to_next
            i += 1
        return mileage

    def get_estimated_time_at_location(self, target_location: Location = None, index: int = None):
        mileage = self.get_estimated_mileage_at_location(target_location=target_location, index=index)
        return TimeConversion.convert_miles_to_time(mileage, start_time=self.start_time, pause_seconds=0)

    def assigned_truck_location_total(self):
        return len([location for location in self.ordered_route if location.has_required_truck_package])

    def delayed_location_total(self):
        return len([location for location in self.ordered_route if location.has_delayed_packages()])

    def bundled_location_total(self):
        return len([location for location in self.ordered_route if location.has_bundled_package])

    def early_deadline_total(self):
        return len([location for location in self.ordered_route if location.has_early_deadline()])

    def unconfirmed_location_total(self):
        return len([location for location in self.ordered_route if location.has_unconfirmed_package])
