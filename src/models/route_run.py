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
    """
    Class representing a route run.

    Attributes:
        _target_location (Location or None): The target location of the route run.
        _start_time (time): The start time of the route run.
        _estimated_completion_time (time or None): The estimated completion time of the route run.
        _requirements_met (bool or None): Flag indicating if the requirements of the route run are met.
        _estimated_mileage (float): The estimated mileage of the route run.
        _ordered_route (list): The ordered list of locations in the route run.
        _required_packages (set): The set of required packages for the route run.
        _locations (set): The set of locations in the route run.
        _assigned_truck_id (int or None): The ID of the assigned truck for the route run.
        _return_to_hub (bool): Flag indicating if the route run returns to the hub.
        _focused_run (RunFocus or None): The focus of the route run.
        _run_analysis_dict (dict or None): Dictionary storing the analysis of the route run.
        _error_location (Location or None): The location where an error occurred in the route run.
        _error_type (None or str): The type of error that occurred in the route run.
    """
    def __init__(self, return_to_hub: bool = False, start_time: time = config.DELIVERY_DISPATCH_TIME):
        """
        Initializes a RouteRun object.

        Args:
            return_to_hub (bool): Indicates if the route run returns to the hub.
            start_time (time): The start time of the route run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

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

    def __eq__(self, other):
        """
        Checks if two RouteRun objects are equal.

        Args:
            other (RouteRun): The other RouteRun object to compare.

        Returns:
            bool: True if the objects are equal, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if isinstance(other, self.__class__):
            return self.start_time == other.start_time
        return NotImplemented

    def __lt__(self, other):
        """
        Compares if a RouteRun object is less than another RouteRun object.

        Args:
            other (RouteRun): The other RouteRun object to compare.

        Returns:
            bool: True if the object is less than the other object, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if isinstance(other, self.__class__):
            return self.start_time < other.start_time
        return NotImplemented

    def __gt__(self, other):
        """
        Compares if a RouteRun object is greater than another RouteRun object.

        Args:
            other (RouteRun): The other RouteRun object to compare.

        Returns:
            bool: True if the object is greater than the other object, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if isinstance(other, self.__class__):
            return self.start_time > other.start_time
        return NotImplemented

    def __hash__(self):
        """
        Generates a hash value for the RouteRun object.

        Returns:
            int: The hash value.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return hash((self.start_time, self.estimated_completion_time))

    @property
    def target_location(self):
        """
        Getter property for the target location of the route run.

        Returns:
            Location: The target location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._target_location

    @property
    def start_time(self):
        """
        Getter property for the start time of the route run.

        Returns:
            time: The start time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._start_time

    @property
    def estimated_completion_time(self):
        """
        Getter property for the estimated completion time of the route run.

        Returns:
            time: The estimated completion time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._estimated_completion_time

    @property
    def requirements_met(self):
        """
        Getter property for the status of requirements being met for the route run.

        Returns:
            bool: True if the requirements are met, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._requirements_met

    @property
    def estimated_mileage(self):
        """
        Getter property for the estimated mileage of the route run.

        Returns:
            float: The estimated mileage.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._estimated_mileage

    @property
    def ordered_route(self):
        """
        Getter property for the ordered route of the route run.

        Returns:
            List[Location]: The ordered route.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._ordered_route

    @property
    def required_packages(self):
        """
        Getter property for the required packages of the route run.

        Returns:
            Set[Package]: The required packages.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._required_packages

    @property
    def return_to_hub(self):
        """
        Getter property for the return_to_hub flag of the route run.

        Returns:
            bool: True if the route run returns to the hub, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._return_to_hub

    @property
    def locations(self):
        """
        Getter property for the locations of the route run.

        Returns:
            Set[Location]: The locations.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._locations

    @property
    def assigned_truck_id(self):
        """
        Getter property for the assigned truck ID of the route run.

        Returns:
            int: The assigned truck ID.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._assigned_truck_id

    @property
    def focused_run(self):
        """
        Getter property for the focused run of the route run.

        Returns:
            RunFocus: The focused run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._focused_run

    @property
    def run_analysis_dict(self):
        """
        Getter property for the run analysis dictionary of the route run.

        Returns:
            dict: The run analysis dictionary.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._run_analysis_dict

    @property
    def error_location(self):
        """
        Getter property for the error location of the route run.

        Returns:
            Location: The error location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._error_location

    @property
    def error_type(self):
        """
        Getter property for the error type of the route run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._error_type

    @target_location.setter
    def target_location(self, value: Location):
        """
        Setter property for the target location of the route run.

        Args:
            value (Location): The target location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._target_location = value

    @start_time.setter
    def start_time(self, value: time):
        """
        Setter property for the start time of the route run.

        Args:
            value (time): The start time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._start_time = value

    @ordered_route.setter
    def ordered_route(self, value: Set[Location]):
        """
        Setter property for the ordered route of the route run.

        Args:
            value (Set[Location]): The ordered route.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._ordered_route = value

    @requirements_met.setter
    def requirements_met(self, value: bool):
        """
        Setter property for the status of requirements being met for the route run.

        Args:
            value (bool): The status of requirements being met.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._requirements_met = value

    @locations.setter
    def locations(self, value: Set[Location]):
        """
        Setter property for the locations of the route run.

        Args:
            value (Set[Location]): The locations.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._locations = value

    @assigned_truck_id.setter
    def assigned_truck_id(self, value: int):
        """
        Setter property for the assigned truck ID of the route run.

        Args:
            value (int): The assigned truck ID.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._assigned_truck_id = value

    @focused_run.setter
    def focused_run(self, value: RunFocus):
        """
        Setter property for the focused run of the route run.

        Args:
            value (RunFocus): The focused run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._focused_run = value

    @required_packages.setter
    def required_packages(self, value):
        """
        Setter property for the required packages of the route run.

        Args:
            value: The required packages.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._required_packages = value

    @run_analysis_dict.setter
    def run_analysis_dict(self, value: dict):
        """
        Setter property for the run analysis dictionary of the route run.

        Args:
            value (dict): The run analysis dictionary.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._run_analysis_dict = value

    @error_location.setter
    def error_location(self, value: Location):
        """
        Setter property for the error location of the route run.

        Args:
            value (Location): The error location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._error_location = value

    @error_type.setter
    def error_type(self, value):
        """
        Setter property for the error type of the route run.

        Args:
            value: The error type.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._error_type = value

    def package_total(self, alternate_locations: Set[Location] = None):
        """
        Returns the total number of packages in the route run.

        Args:
            alternate_locations (Set[Location], optional): Set of alternate locations to consider. Defaults to None.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return len(self.get_all_packages(alternate_locations))

    def set_estimated_mileage(self):
        """
        Sets the estimated mileage of the route run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._estimated_mileage = self.get_estimated_mileage_at_location(index=len(self.ordered_route) - 1)

    def set_estimated_completion_time(self):
        """
        Sets the estimated completion time of the route run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._estimated_completion_time = TimeConversion.convert_miles_to_time(self._estimated_mileage,
                                                                               self._start_time, pause_seconds=0)

    def set_assigned_truck_id(self):
        """
        Sets the assigned truck ID for the route run based on the packages at each location in the ordered route.

        Raises:
            InvalidRouteRunError: If there are conflicting assigned truck IDs for the packages in the route run.

        Time Complexity: O(n * m)
        Space Complexity: O(1)
        """

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
        """
        Sets the required packages for the route run by aggregating packages from each location in the route run.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        for location in self.locations:
            if location.is_hub:
                continue
            self.required_packages.update(location.package_set)
        for package in PackageHandler.get_bundled_packages(ignore_assigned=False):
            if package in self.required_packages:
                self.required_packages.update(PackageHandler.get_bundled_packages(ignore_assigned=True))

    def get_all_packages(self, alternate_locations: Set[Location] = None):
        """
        Retrieves all the packages in the route run, considering optional alternate locations.

        Args:
            alternate_locations (Set[Location], optional): Set of alternate locations to consider. Defaults to None.

        Returns:
            Set[Package]: All the packages in the route run.

        Time Complexity: O(n * m)
        Space Complexity: O(n * m)
        """

        all_packages = set()
        for location in (alternate_locations if alternate_locations else self.locations):
            if location.is_hub:
                continue
            all_packages.update(location.package_set)
        return all_packages

    def get_estimated_mileage_at_location(self, target_location: Location = None, index: int = None):
        """
        Calculates the estimated mileage from the start location to the target location or
            a specific index in the route run.

        Args:
            target_location (Location, optional): The target location. Defaults to None.
            index (int, optional): The index of the location in the route run. Defaults to None.

        Returns:
            float: The estimated mileage.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

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