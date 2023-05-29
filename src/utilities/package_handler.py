from copy import copy
from datetime import time
from typing import Set, Tuple

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.exceptions import DelayedPackagesArrivedException, AddressUpdateException
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash
from src.utilities.time_conversion import TimeConversion

__all__ = ['PackageHandler']


def _is_package_arriving_at_hub(package: Package, current_time: time) -> bool:
    """
    Checks if a package is arriving at the hub based on its status and the current time.

    Args:
        package (Package): The package to check.
        current_time (time): The current time.

    Returns:
        bool: True if the package is arriving at the hub, False otherwise.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    return (package.status is DeliveryStatus.ON_ROUTE_TO_DEPOT and
            TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time))


def _is_package_address_updating(package: Package, current_time: time) -> bool:
    """
    Checks if a package's address is being updated based on the current time and package properties.

    Args:
        package (Package): The package to check.
        current_time (time): The current time.

    Returns:
        bool: True if the package's address is being updated, False otherwise.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    return (TimeConversion.is_time_at_or_before_other_time(config.PACKAGE_9_ADDRESS_CHANGE_TIME, current_time) and
            not package.is_verified_address)


class PackageHandler:
    """
    A class that handles the management and operations related to packages.

    Attributes:
        all_locations (Tuple[Location]): A tuple of all locations.
        all_packages (Tuple[Package]): A tuple of all packages.
        package_hash (CustomHash): A custom hash data structure used for package lookup.
        Truck.hub_location (Location): The hub location for the trucks.
    """

    all_locations: Tuple[Location] = CsvParser.initialize_locations()
    all_packages: Tuple[Package] = CsvParser.initialize_packages(all_locations)
    package_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
    package_hash.add_all_packages(all_packages)
    Truck.hub_location = [location for location in all_locations if location.is_hub][0]

    @staticmethod
    def update_delivery_location(current_time: time, locations_list: Tuple[Location],
                                 package: Package, updated_address: str):
        """
        Updates the delivery location of a package based on the updated address.

        Args:
            current_time (time): The current time.
            locations_list (Tuple[Location]): A tuple of all locations.
            package (Package): The package to update.
            updated_address (str): The updated address for the package.

        Returns:
            bool: True if the delivery location was successfully updated, False otherwise.

        Time Complexity: O(n)
        Space Complexity: O(1)

        Raises:
            AddressUpdateException: If the package's location is successfully updated.
        """

        try:
            address, city, state_zip = updated_address.split(', ')
            zip_code = int(state_zip.split(' ')[1])
            for location in locations_list:
                if str(address).startswith(location.address) and location.zip_code == zip_code:
                    old_location = package.location
                    old_location.package_set.remove(package)
                    package.location = location
                    package.location.package_set.add(package)
                    package.is_verified_address = True
                    package.special_note = '\u001b[9m' + package.special_note + '\033[0m'
                    package.update_status(package.status, current_time)
                    raise AddressUpdateException(package, old_location)
        except (ValueError, TypeError):
            return False
        return False

    @staticmethod
    def bulk_status_update(current_time: time, packages=all_packages):
        """
        Performs a bulk status update for packages based on the current time.

        Args:
            current_time (time): The current time.
            packages (Tuple[Package]): The packages to update. Defaults to all_packages.

        Raises:
            DelayedPackagesArrivedException: If delayed packages have arrived.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        delayed_packages_arrived = False
        for package in packages:
            if _is_package_arriving_at_hub(package, current_time):
                package.update_status(DeliveryStatus.AT_HUB, current_time)
                delayed_packages_arrived = True
            if _is_package_address_updating(package, current_time):
                PackageHandler.update_delivery_location(current_time, PackageHandler.all_locations, package,
                                                        config.EXCEPTED_UPDATES[package.package_id]['address'])
        if delayed_packages_arrived:
            raise DelayedPackagesArrivedException

    @staticmethod
    def get_bundled_packages(locations=all_locations, all_location_packages=False,
                             ignore_assigned=False) -> Set[Package]:
        """
        Retrieves bundled packages from specified locations.

        Args:
            locations (Tuple[Location]): Tuple of locations to search for bundled packages (default: all_locations).
            all_location_packages (bool): Flag to include all packages at the location (default: False).
            ignore_assigned (bool): Flag to ignore packages assigned to a truck (default: False).

        Returns:
            Set[Package]: Set of bundled packages.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        package_bundle_set = set()
        for location in locations:
            if location.has_bundled_package:
                for package in location.package_set:
                    if package.bundled_package_set:
                        package_bundle_set.update(package.bundled_package_set)
        if ignore_assigned:
            non_assigned_set = copy(package_bundle_set)
            for package in package_bundle_set:
                if package.location.been_assigned:
                    non_assigned_set -= package.location.package_set
            package_bundle_set = non_assigned_set
        if all_location_packages:
            full_set = set()
            for package in package_bundle_set:
                full_set.update(package.location.package_set)
            package_bundle_set = full_set
        return package_bundle_set

    @staticmethod
    def get_delayed_packages(packages=all_packages, ignore_arrived=False) -> Set[Package]:
        """
        Retrieves delayed packages based on the hub arrival time and delivery dispatch time.

        Args:
            packages (Tuple[Package]): Tuple of packages to check for delayed packages (default: all_packages).
            ignore_arrived (bool): Flag to ignore packages that have arrived at the hub (default: False).

        Returns:
            Set[Package]: Set of delayed packages.

        Time Complexity: O(n)
        Space Complexity: O(n)

        """

        delayed_packages = set()
        for package in packages:
            if (TimeConversion.get_datetime(package.hub_arrival_time) >
                    TimeConversion.get_datetime(config.DELIVERY_DISPATCH_TIME)):
                if ignore_arrived and package.status == DeliveryStatus.AT_HUB:
                    continue
                delayed_packages.add(package)
        return delayed_packages

    @staticmethod
    def get_assigned_truck_packages(truck_id: int = None, packages=all_packages):
        """
        Retrieves packages assigned to a specific truck.

        Args:
            truck_id (int): ID of the truck to filter by (default: None).
            packages (Tuple[Package]): Tuple of packages to search for assigned truck packages (default: all_packages).

        Returns:
            Set[Package]: Set of packages assigned to the specified truck.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        truck_packages = set()
        for package in packages:
            if package.assigned_truck_id:
                if not truck_id or truck_id == package.assigned_truck_id:
                    truck_packages.add(package)
        return truck_packages

    @staticmethod
    def get_all_expected_status_update_times(special_times=None, start_time=config.PACKAGE_ARRIVAL_STATUS_UPDATE_TIME,
                                             end_time=config.DELIVERY_RETURN_TIME, in_locations=all_locations):
        """
        Retrieves all expected status update times based on the provided parameters.

        Args:
            special_times (set, optional): A set of special times. Defaults to None.
            start_time (time, optional): The start time for status updates.
                Defaults to config.PACKAGE_ARRIVAL_STATUS_UPDATE_TIME.
            end_time (time, optional): The end time for status updates. Defaults to config.DELIVERY_RETURN_TIME.
            in_locations (Tuple[Location], optional): The locations to consider. Defaults to all_locations.

        Returns:
            set: A set of all expected status update times.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        status_updates_times = set()
        if special_times:
            status_updates_times = status_updates_times.union(special_times)
        start_date_time = TimeConversion.get_datetime(start_time)
        end_date_time = TimeConversion.get_datetime(end_time)
        for location in in_locations:
            if location.earliest_deadline:
                earliest_deadline = TimeConversion.get_datetime(location.earliest_deadline)
                if start_date_time <= earliest_deadline < end_date_time:
                    status_updates_times.add(earliest_deadline.time())
            if location.latest_package_arrival:
                latest_package_arrival_time = TimeConversion.get_datetime(location.latest_package_arrival)
                if start_date_time <= latest_package_arrival_time < end_date_time:
                    status_updates_times.add(latest_package_arrival_time.time())
        return status_updates_times

    @staticmethod
    def get_package_locations(in_packages: Set[Package], ignore_assigned=False) -> Set[Location]:
        """
        Retrieves the locations of the given packages.

        Args:
            in_packages (Set[Package]): The set of packages to retrieve locations for.
            ignore_assigned (bool, optional): Whether to ignore packages with assigned locations. Defaults to False.

        Returns:
            Set[Location]: A set of locations.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        locations = set()
        for package in in_packages:
            if not ignore_assigned or not package.location.been_assigned:
                locations.add(package.location)
        return locations

    @staticmethod
    def get_available_packages(current_time: time, in_packages=all_packages, ignore_assigned=False) -> Set[Package]:
        """
        Retrieves the available packages based on the current time.

        Args:
            current_time (time): The current time.
            in_packages (Tuple[Package], optional): The packages to consider. Defaults to all_packages.
            ignore_assigned (bool, optional): Whether to ignore packages with assigned locations. Defaults to False.

        Returns:
            Set[Package]: A set of available packages.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        available_packages = set()
        for package in in_packages:
            if package.location.been_assigned and ignore_assigned:
                continue
            if TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time):
                available_packages.add(package)
        return available_packages

    @staticmethod
    def get_unconfirmed_packages(in_packages=all_packages):
        """
        Retrieves the unconfirmed packages from the given packages.

        Args:
            in_packages (Tuple[Package], optional): The packages to consider. Defaults to all_packages.

        Returns:
            Set[Package]: A set of unconfirmed packages.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        unconfirmed_packages = set()
        for package in in_packages:
            if not package.is_verified_address:
                unconfirmed_packages.add(package)
        return unconfirmed_packages

    @staticmethod
    def get_package_snapshot(package: Package, target_time: time) -> Package:
        """
        Retrieves a snapshot of the package at the target time.

        Args:
            package (Package): The package to take a snapshot of.
            target_time (time): The target time for the snapshot.

        Returns:
            Package: A snapshot of the package at the target time.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        snapshot_package = copy(package)
        update_time, snapshot_update = package.find_package_state_at_time(target_time)
        snapshot_package.location = snapshot_update['location']
        snapshot_package.status = snapshot_update['status']
        snapshot_package.special_note = snapshot_update['special_note']
        snapshot_package.is_verified_address = snapshot_update['is_verified_address']
        return snapshot_package
