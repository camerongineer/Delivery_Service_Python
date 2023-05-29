import math
from copy import copy
from datetime import time

__all__ = ['Package']

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location


def _get_formatted_status_string(update, package, formatted_address, status):
    """
    Time complexity: O(1)
    Space complexity: O(1)
    """
    return (f'{update} | Package ID: {str(package.package_id).zfill(2)} |'
            f' Destination: {formatted_address} | Status: "{status}"')


class Package:
    """
    Class representing a package.

    Attributes:
        package_id (int): Identifier of the package.
        location (Location): Location object representing the package's destination.
        is_verified_address (bool): Flag indicating if the package's address is verified.
        deadline (time): Deadline for package delivery.
        weight (float): Weight of the package.
        status (DeliveryStatus): Current delivery status of the package.
        special_note (str): Special note associated with the package.
        status_update_dict (dict): Dictionary storing the package's status updates.
        bundled_package_set (set): Set of bundled packages associated with the package.
        assigned_truck_id (None or int): ID of the truck assigned to deliver the package.
        bundled_package_ids (None or list): List of bundled package IDs.
        pending_update_time (None or time): Time of the pending status update.
        hub_arrival_time (None or time): Time of arrival at the hub.
        hub_departure_time (None or time): Time of departure from the hub.
        delivery_time (None or time): Time of package delivery.
    """

    def __init__(self, package_id: int, location: Location, is_verified_address, deadline, weight, special_note):
        self.package_id = package_id
        self.location = location
        self.is_verified_address = is_verified_address
        self.deadline = deadline
        self.weight = weight
        self.status = DeliveryStatus.ON_ROUTE_TO_DEPOT
        self.special_note = special_note
        self.status_update_dict = dict()
        self.bundled_package_set = set()
        self.assigned_truck_id = None
        self.bundled_package_ids = None
        self.pending_update_time = None
        self.hub_arrival_time = None
        self.hub_departure_time = None
        self.delivery_time = None

    def __hash__(self):
        """
        Returns the hash value of the package based on its package ID.

        Returns:
            int: The hash value of the package.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return hash(self.package_id)

    def __str__(self):
        """
        Returns a string representation of the package.

        Returns:
            str: A string representation of the package.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return f'Package ID: {self.package_id}\n' \
               f'Location Name: {self.location.name}\n' \
               f'Address: {self.location.get_full_address()}\n' \
               f'Delivery Deadline: {self.deadline}\n' \
               f'Weight: {self.weight} ' + ('lbs.' if self.weight != 1 else 'lb.') + '\n' \
               f'Verified Address: ' + ("Yes" if self.is_verified_address else "No") + \
               (f'\nSpecial Notes: {self.special_note}' if self.special_note else '')

    def __repr__(self):
        """
        Returns a string representation of the package that can be used to recreate the package object.

        Returns:
            str: A string representation of the package.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return f"Package(package_id={self.package_id}, Location: {self.location.name} - {self.location.address}" \
               f" - is_verified_address={self.is_verified_address}," \
               f" deadline=datetime.strptime('{self.deadline}', '%I:%M:%S'), weight={self.weight}," \
               f" status={self.status}, special_note='{self.special_note}')"

    def __eq__(self, other):
        """
        Compares the package with another package or location for equality.

        Args:
            other: The package or location to compare with.

        Returns:
            bool: True if the packages or locations are equal, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return self.location is other.location or \
            math.isclose((self.location.distance_dict.values()), sum(other.location.distance_dict.values()))

    def __lt__(self, other):
        """
        Compares the package with another package based on their total distance.

        Args:
            other: The package to compare with.

        Returns:
            bool: True if the package is less than the other package, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return sum(self.location.distance_dict.values()) < sum(other.location.distance_dict.values())

    def __gt__(self, other):
        """
        Compares the package with another package based on their total distance.

        Args:
            other: The package to compare with.

        Returns:
            bool: True if the package is greater than the other package, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return sum(self.location.distance_dict.values()) > sum(other.location.distance_dict.values())

    def __le__(self, other):
        """
        Compares the package with another package or location based on their total distance.

        Args:
            other: The package or location to compare with.

        Returns:
            bool: True if the package is less than or equal to the other package or location, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return self.location is other.location or \
            sum(self.location.distance_dict.values()) <= sum(other.location.distance_dict.values())

    def __ge__(self, other):
        """
        Compares the package with another package or location based on their total distance.

        Args:
            other: The package or location to compare with.

        Returns:
            bool: True if the package is greater than or equal to the other package or location, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return self.location is other.location or \
            sum(self.location.distance_dict.values()) >= sum(other.location.distance_dict.values())

    def update_status(self, updated_status: DeliveryStatus, current_time: time):
        """
        Updates the status of the package with the provided status and current time.

        Args:
            updated_status (DeliveryStatus): The updated status of the package.
            current_time (time): The current time.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.status = updated_status
        if current_time not in self.status_update_dict:
            self.status_update_dict[current_time] = {'status': copy(updated_status), 'location': self.location,
                                                     'is_verified_address': self.is_verified_address,
                                                     'special_note': self.special_note}
        else:
            if self.status_update_dict[current_time]['status'] is not updated_status:
                if (isinstance(self.status_update_dict[current_time]['status'], tuple) and
                        updated_status not in self.status_update_dict[current_time]['status']):
                    self.status_update_dict[current_time]['status'] += (updated_status,)
                else:
                    self.status_update_dict[current_time]['status'] =\
                        self.status_update_dict[current_time]['status'], updated_status

    def get_full_address(self) -> str:
        """
        Returns the full address of the package.

        Returns:
            str: The full address of the package.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return f'{self.location}'

    def get_status_string(self, current_time, address_length=None):
        """
        Returns the status string of the package at the given current time.

        Args:
            current_time: The current time.
            address_length (int, optional): The length to which the address should be formatted. Defaults to None.

        Returns:
            str: The status string of the package.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        if current_time:
            last_update, package_state = self.find_package_state_at_time(current_time)
            status = package_state['status']
            location = package_state['location']
        else:
            status = self.status
            location = self.location
            last_update = list(self.status_update_dict.keys())[-1]
        address = location.get_full_address()
        if not address_length:
            address_length = max([len(_location.get_full_address()) for _location in [location, self.location]])
        formatted_address = ('{:^' + str(address_length) + '}').format(address)
        if isinstance(status, tuple):
            appended_status = []
            for tuple_status in reversed(status):
                appended_status.append(_get_formatted_status_string(last_update, self, formatted_address, tuple_status))
            return '\n'.join(appended_status)
        return _get_formatted_status_string(last_update, self, formatted_address, status)

    def find_package_state_at_time(self, current_time: time):
        """
        Finds the package state at the given current time.

        Args:
            current_time (time): The current time.

        Returns:
            Tuple[time, dict]: The latest update time and the package state at that time.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        latest_update_time = config.STANDARD_PACKAGE_ARRIVAL_TIME
        for update_time, values in self.status_update_dict.items():
            if current_time >= update_time:
                latest_update_time = update_time
                continue
            else:
                break
        return latest_update_time, self.status_update_dict[latest_update_time]
