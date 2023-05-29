__all__ = ['Location']

from datetime import time

from src import config
from src.config import DELIVERY_RETURN_TIME
from src.constants.states import State
from src.constants.utah_cities import UtahCity


class Location:
    """
    Class representing a location.

    Attributes:
        name (str): Name of the location.
        address (str): Address of the location.
        is_hub (bool): Flag indicating if the location is a hub.
        _city (UtahCity): City where the location is located.
        _state (State): State where the location is located.
        zip_code (int): Zip code of the location.
        distance_dict (dict): Dictionary containing distances to other locations.
        package_set (set): Set of packages associated with the location.
        _hub_distance (float): Distance from the location to the hub.
        been_visited (bool): Flag indicating if the location has been visited.
        been_assigned (bool): Flag indicating if the location has been assigned.
        been_routed (bool): Flag indicating if the location has been routed.
        assigned_truck_id (None or int): ID of the truck assigned to the location.
        earliest_deadline (time): Earliest deadline for package delivery.
        latest_package_arrival (None or time): Latest time for package arrival.
        has_required_truck_package (bool): Flag indicating if the location has a required truck package.
        has_unconfirmed_package (bool): Flag indicating if the location has an unconfirmed package.
        has_bundled_package (bool): Flag indicating if the location has a bundled package.
    """

    def __init__(self, name: str, address: str, is_hub=False):
        """
        Initializes a new instance of the Location class.

        Args:
            name (str): The name of the location.
            address (str): The address of the location.
            is_hub (bool, optional): Indicates whether the location is a hub. Defaults to False.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.name = name
        self.address = address
        self._city = None
        self._state = None
        self._zip_code = None
        self.distance_dict = dict()
        self.package_set = set()
        self.is_hub = is_hub
        self._hub_distance = None
        self.been_visited = False
        self.been_assigned = False
        self.been_routed = False
        self.assigned_truck_id = None
        self.earliest_deadline = DELIVERY_RETURN_TIME
        self.latest_package_arrival = None
        self.has_required_truck_package = False
        self.has_unconfirmed_package = False
        self.has_bundled_package = False

    def __eq__(self, other):
        """
        Checks if the current location is equal to another location.

        Args:
            other: The other location to compare with.

        Returns:
            bool: True if the locations are equal, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if isinstance(other, Location):
            return self.address == other.address and self.name == other.name and self.zip_code == other.zip_code
        return False

    def __hash__(self):
        """
        Returns the hash value of the location based on its address and name.

        Returns:
            int: The hash value of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return hash(self.address + self.name)

    def __contains__(self, item):
        """
        Checks if a package is present in the location's package set.

        Args:
            item: The package to check for.

        Returns:
            bool: True if the package is present, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return item in self.package_set

    def __lt__(self, other):
        """
        Compares the location with another location based on their hub distances.

        Args:
            other: The location to compare with.

        Returns:
            bool: True if the location is less than the other location, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.hub_distance < other.hub_distance

    def __gt__(self, other):
        """
        Compares the location with another location based on their hub distances.

        Args:
            other: The location to compare with.

        Returns:
            bool: True if the location is greater than the other location, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.hub_distance > other.hub_distance

    def __repr__(self):
        """
        Returns a string representation of the location that can be used to recreate the location object.

        Returns:
            str: A string representation of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return f"Location(name='{self.name}', address='{self.address}', is_hub={self.is_hub})"

    @property
    def city(self):
        """
        Getter property for the city of the location.

        Returns:
            UtahCity: The city of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._city

    @property
    def state(self):
        """
        Getter property for the state of the location.

        Returns:
            State: The state of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._state

    @property
    def zip_code(self):
        """
        Getter property for the zip code of the location.

        Returns:
            int: The zip code of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._zip_code

    @property
    def hub_distance(self):
        """
        Getter property for the distance from the location to the hub.

        Returns:
            float: The distance from the location to the hub.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._hub_distance

    @city.setter
    def city(self, value: UtahCity):
        """
        Setter property for the city of the location.

        Args:
            value (UtahCity): The city of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._city = value

    @state.setter
    def state(self, value: State):
        """
        Setter property for the state of the location.

        Args:
            value (State): The state of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._state = value

    @zip_code.setter
    def zip_code(self, value: int):
        """
        Setter property for the zip code of the location.

        Args:
            value (int): The zip code of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._zip_code = value

    @hub_distance.setter
    def hub_distance(self, value: float):
        """
        Setter property for the distance from the location to the hub.

        Args:
            value (float): The distance from the location to the hub.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._hub_distance = value

    def set_zip_code(self, zip_code: int):
        """
        Sets the zip code of the location.

        Args:
            zip_code (int): The zip code to set.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.zip_code = zip_code

    def set_location_as_hub(self):
        """
        Sets the location as a hub.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.is_hub = True

    def set_distance_dict(self, distance_dict):
        """
        Sets the distance dictionary for the location.

        Args:
            distance_dict: The distance dictionary to set.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.distance_dict = distance_dict

    def set_earliest_deadline(self, deadline: time):
        """
        Sets the earliest deadline for the location.

        Args:
            deadline (time): The earliest deadline to set.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.earliest_deadline = deadline

    def has_early_deadline(self):
        """
        Checks if the location has an early deadline.

        Returns:
            bool: True if the location has an early deadline, False otherwise.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if not self.earliest_deadline:
            return False
        return self.earliest_deadline != config.DELIVERY_RETURN_TIME

    def package_total(self):
        """
        Returns the total number of packages at the location.

        Returns:
            int: The total number of packages at the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if not self.package_set:
            return 0
        return len(self.package_set)

    def distance(self, other_location):
        """
        Calculates the distance between the current location and another location.

        Args:
            other_location: The other location.

        Returns:
            Optional[float]: The distance between the locations, or None if they are the same.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if self is other_location:
            return None
        return self.distance_dict[other_location]

    def get_full_address(self):
        """
        Returns the full address of the location.

        Returns:
            str: The full address of the location.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return f'{self.address}, {self.city.displayed_name}, {self.state.abbreviation} {self.zip_code}'
