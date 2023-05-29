from datetime import time

__all__ = ['Truck']

from typing import Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.exceptions import TruckCapacityExceededError, PackageNotOnTruckError
from src.models.location import Location
from src.models.package import Package
from src.utilities.custom_hash import CustomHash


class Truck(CustomHash):
    """
    Class representing a truck with its associated attributes and methods.

    Attributes:
        hub_location (None or Location): Location object representing the hub location.
        _truck_id (int): Identifier of the truck.
        _clock (time): Current time of the truck.
        _is_dispatched (bool): Flag indicating if the truck has been dispatched.
        _dispatch_time (None or time): Time of dispatch.
        _previous_location (None or Location): Previous location of the truck.
        _current_location (Location): Current location of the truck.
        _next_location (None or Location): Next location of the truck.
        _route_runs (list): List of runs in the truck's route.
        _current_run (None or Run): Current run associated with the truck.
    """

    hub_location = None

    def __init__(self, truck_id: int):
        """
        Initializes a Truck object with the given truck ID.

        Args:
            truck_id (int): The ID of the truck.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(config.NUM_TRUCK_CAPACITY)
        self._truck_id = truck_id
        self._clock = time.min
        self._is_dispatched = False
        self._dispatch_time = None
        self._previous_location = None
        self._current_location = Truck.hub_location
        self._next_location = None
        self._current_run = None
        self._route_runs = list()

    @property
    def truck_id(self):
        """
        Getter property for the truck ID.

        Returns:
            int: The truck ID.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._truck_id

    @property
    def clock(self):
        """
        Getter property for the truck clock.

        Returns:
            time: The truck clock.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._clock

    @property
    def dispatch_time(self):
        """
        Getter property for the truck dispatch time.

        Returns:
            time: The truck dispatch time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._dispatch_time

    @property
    def previous_location(self):
        """
        Getter property for the truck's previous location.

        Returns:
            Location: The previous location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._previous_location

    @property
    def current_location(self):
        """
        Getter property for the truck's current location.

        Returns:
            Location: The current location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._current_location

    @property
    def next_location(self):
        """
        Getter property for the truck's next location.

        Returns:
            Location: The next location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._next_location

    @property
    def current_run(self):
        """
        Getter property for the truck's current run.

        Returns:
            RouteRun: The current run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._current_run

    @property
    def route_runs(self):
        """
        Getter property for the list of route runs associated with the truck.

        Returns:
            list[RouteRun]: The list of route runs.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._route_runs

    @dispatch_time.setter
    def dispatch_time(self, value: time):
        """
        Setter property for the truck's dispatch time.

        Args:
            value (time): The new value for the dispatch time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if not self._dispatch_time:
            self._dispatch_time = value

    @previous_location.setter
    def previous_location(self, value: Location):
        """
        Setter property for the truck's previous location.

        Args:
            value (Location): The new value for the previous location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._previous_location = value

    @current_location.setter
    def current_location(self, value: Location):
        """
        Setter property for the truck's current location.

        Args:
            value (Location): The new value for the current location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._current_location = value

    @next_location.setter
    def next_location(self, value: Location):
        """
        Setter property for the truck's next location.

        Args:
            value (Location): The new value for the next location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._next_location = value

    @current_run.setter
    def current_run(self, value):
        """
        Setter property for the truck's current run.

        Args:
            value (RouteRun): The new value for the current run.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._current_run = value

    def set_clock(self, start_time: time):
        """
        Sets the clock of the truck to the specified start time.

        Args:
            start_time (time): The start time to set.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._clock = start_time

    def add_package(self, package: Package, is_simulated_load=True):
        """
        Adds a package to the truck.

        Args:
            package (Package): The package to add.
            is_simulated_load (bool): Indicates if the package addition is simulated.

        Raises:
            TruckCapacityExceededError: If the truck's capacity is exceeded.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if self._size > config.NUM_TRUCK_CAPACITY:
            raise TruckCapacityExceededError
        if not is_simulated_load:
            package.update_status(DeliveryStatus.LOADED, self.clock)
        super().add_package(package)

    def dispatch(self):
        """
        Dispatches the truck, marking the current time as the dispatch time and updating the status of the
            required packages for the current run to "OUT_FOR_DELIVERY".

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        if not self._is_dispatched:
            self._dispatch_time = self.clock
            self._is_dispatched = True
        for package in self.current_run.required_packages:
            package.update_status(DeliveryStatus.OUT_FOR_DELIVERY, self.clock)

    def deliver(self):
        """
        Delivers packages at the current location, updating their
            status to "DELIVERED" and removing them from the truck.

        Returns:
            Set[Package]: The set of delivered packages.

        Raises:
            PackageNotOnTruckError: If a package to be delivered is not on the truck.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        delivered_packages = set()
        if not self.current_location or self.current_location.is_hub:
            return delivered_packages
        for package in self.current_location.package_set:
            delivered_package = self.get_package(package.package_id)
            if not delivered_package:
                raise PackageNotOnTruckError
            package.update_status(DeliveryStatus.DELIVERED, self.clock)
            package.delivery_time = self.clock
            self.remove_package(package.package_id)
            delivered_packages.add(package)
        return delivered_packages

    def unload(self) -> Set[Package]:
        """
        Unloads all packages from the truck, returning a set of the unloaded packages.

        Returns:
            Set[Package]: The set of unloaded packages.

        Time Complexity: O(n^2)
        Space Complexity: O(n)
        """

        truck_packages = set()
        for slot in self._arr:
            for package in slot:
                truck_packages.add(package)
        self._arr = [[] for _ in range(self._capacity)]
        self._size = 0
        return truck_packages

    def distance(self, origin_location=None, target_location=None, to_hub=False):
        """
        Calculates the distance between two locations.

        Args:
            origin_location (Location): The origin location. If not provided, the current location is used.
            target_location (Location): The target location. If not provided, the next location is used.
            to_hub (bool): Indicates whether the target location is the hub.

        Returns:
            float: The distance between the two locations.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if not origin_location:
            origin_location = self.current_location
        if not target_location:
            target_location = self.next_location
        if to_hub:
            target_location = self.hub_location
        if origin_location and target_location and (origin_location is not target_location):
            return origin_location.distance_dict[target_location]
        return 0

    def is_loaded(self):
        """
        Checks if the truck is loaded with packages.

        Returns:
            bool: True if the truck is loaded, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._size > 0

    def is_package_on_truck(self, package):
        """
        Checks if a package is on the truck.

        Args:
            package (Package): The package to check.

        Returns:
            bool: True if the package is on the truck, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return self._locate_package(package_id=package.package_id) != -1
