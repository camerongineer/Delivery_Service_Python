import csv
import re
from copy import copy
from datetime import datetime, time
from typing import List, Set, Tuple

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.constants.utah_cities import UtahCity
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.time_conversion import TimeConversion

__all__ = ['CsvParser']


def _set_arrival_time(package: Package):
    """
    Sets the hub arrival time for a package based on its special note.

    Args:
        package (Package): The package to set the arrival time for.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    if package.special_note.startswith('Delayed'):
        match = re.search(r'(\d{1,2}):(\d{2})\s+(am|pm)', package.special_note)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if match.group(3) == 'pm' and hour != 12:
                hour += 12
            elif match.group(3) == 'am' and hour == 12:
                hour = 0
            package.hub_arrival_time = time(hour=hour, minute=minute)
            package.update_status(DeliveryStatus.ON_ROUTE_TO_DEPOT, config.STANDARD_PACKAGE_ARRIVAL_TIME)
    else:
        package.hub_arrival_time = config.STANDARD_PACKAGE_ARRIVAL_TIME
        package.update_status(DeliveryStatus.AT_HUB, config.STANDARD_PACKAGE_ARRIVAL_TIME)


def _set_assigned_truck(package: Package):
    """
    Sets the assigned truck for a package based on its special note.

    Args:
        package (Package): The package to set the assigned truck for.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    if package.special_note.startswith('Can only be on truck '):
        pattern = r'\d+'
        match = re.findall(pattern, package.special_note).pop()
        package.assigned_truck_id = int(match)
        package.location.has_required_truck_package = True
        package.location.assigned_truck_id = package.assigned_truck_id


def _set_earliest_location_deadline(location: Location, in_deadline_time: time):
    """
    Sets the earliest deadline for a location based on the given deadline time.

    Args:
        location (Location): The location to set the earliest deadline for.
        in_deadline_time (time): The new deadline time.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    current_location_deadline = TimeConversion.get_datetime(location.earliest_deadline)
    in_deadline = TimeConversion.get_datetime(in_deadline_time)
    if in_deadline < current_location_deadline:
        location.earliest_deadline = in_deadline_time


def _set_latest_location_package_arrival(location: Location, in_arrival_time: time):
    """
    Sets the latest package arrival time for a location based on the given arrival time.

    Args:
        location (Location): The location to set the latest package arrival time for.
        in_arrival_time (time): The new arrival time.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    if not location.latest_package_arrival:
        location.latest_package_arrival = in_arrival_time
    else:
        current_latest_location_arrival = TimeConversion.get_datetime(location.latest_package_arrival)
        in_arrival = TimeConversion.get_datetime(in_arrival_time)
        if in_arrival > current_latest_location_arrival:
            location.latest_package_arrival = in_arrival_time


def _set_bundled_packages_ids(package: Package):
    """
    Sets the bundled package IDs for a package based on its special note.

    Args:
        package (Package): The package to set the bundled package IDs for.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    if str(package.special_note).startswith('Must be delivered with '):
        pattern = r'\d+'
        package_ids = [int(match) for match in re.findall(pattern, package.special_note)]
        package.bundled_package_ids = package_ids
        package.location.has_bundled_package = True


def _get_bundle_id_sets(packages: List[Package]) -> List[Set[int]]:
    """
    Returns a list of sets, where each set represents a bundle of package IDs.

    Args:
        packages (List[Package]): The list of packages to group into bundles.

    Returns:
        List[Set[int]]: A list of sets, where each set represents a bundle of package IDs.

    Time Complexity: O(n * m)
    Space Complexity: O(n)
    """

    bundle_id_sets = []
    for package in packages:
        if package.bundled_package_ids:
            if not bundle_id_sets:
                bundle_set = {package.package_id}
                for package_id in package.bundled_package_ids:
                    bundle_set.add(package_id)
                bundle_id_sets.append(bundle_set)
            else:
                for bundle_set in bundle_id_sets:
                    if package.package_id in bundle_set:
                        for package_id in package.bundled_package_ids:
                            bundle_set.add(package_id)
                        break
                    else:
                        bundle_set = {package.package_id}
                        for package_id in package.bundled_package_ids:
                            bundle_set.add(package_id)
                        bundle_id_sets.append(bundle_set)
    return bundle_id_sets


def _union_id_sets(bundle_id_list: List[frozenset]):
    """
    Performs a union operation on a list of sets and returns the resulting set.

    Args:
        bundle_id_list (List[frozenset]): The list of sets to perform the union operation on.

    Returns:
        Set[int]: The resulting set after performing the union operation on the input sets.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    if len(bundle_id_list) == 1:
        return bundle_id_list[0]
    else:
        result = bundle_id_list[0]
        for i in range(1, len(bundle_id_list)):
            result = result.union(bundle_id_list[i])
        return result


def _set_bundled_packages(packages: List[Package]):
    """
    Sets the bundled package information for the given list of packages.

    Args:
        packages (List[Package]): The list of packages to set the bundled package information for.

    Time Complexity: O(n * m * k)
    Space Complexity: O(n + m)
    """

    bundle_id_sets = list(map(frozenset, _get_bundle_id_sets(packages)))
    bundle_id_sets = list(set(bundle_id_sets))
    bundle_id_sets = [{s for s in _union_id_sets(bundle_id_sets)}]
    for id_set in bundle_id_sets:
        for package_id in id_set:
            if type(package_id) is not int:
                continue
            for package in packages:
                if package.package_id == package_id:
                    id_set.remove(package_id)
                    id_set.add(package)
    for bundle_set in bundle_id_sets:
        for package in bundle_set:
            package.bundled_package_set = copy(bundle_set)
            package.location.has_bundled_package = True
            package.bundled_package_set.remove(package)


class CsvParser:
    """Parses CSV files to initialize locations and packages."""

    @staticmethod
    def initialize_locations(filepath=config.DISTANCE_CSV_FILE) -> Tuple[Location]:
        """
        Initializes and returns a list of Location objects based on the data from a CSV file.

        Args:
            filepath (str): The filepath of the CSV file containing location data.

        Returns:
            Tuple[Location]: The tuple of Location objects initialized from the CSV file.

        Time Complexity: O(n^2)
        Space Complexity: O(n^2)
        """

        locations = []
        with open(filepath) as csv_file:
            columns = csv.reader(csv_file).__next__()
            for column in columns[2:]:
                name, address, *overflow = column.split('\n')
                address = address.strip()[:-1] if not str(address[-1]).isalnum() else address.strip()
                location = Location(name.strip(), address)
                if overflow:
                    *city_state, zip_code = overflow[0].split()
                    city_state = ' '.join(city_state)
                    city, *state = city_state.split(', ')
                    for utah_city in UtahCity:
                        if utah_city.displayed_name == city:
                            location.city = utah_city
                            location.state = utah_city.state
                            break
                    location.zip_code = int(zip_code)
                locations.append(location)

            name_address_rows = []
            address_zip_rows = []
            distances_rows = []
            for csv_row in csv.reader(csv_file):
                name_address, address_zip, *distances = csv_row
                name_address_rows.append(name_address)
                address_zip_rows.append(address_zip)
                distances_rows.append(distances)

            for i, row in enumerate(distances_rows):
                name = str(name_address_rows[i].split('\n')[0]).strip()
                if str(address_zip_rows[i]).strip() == 'HUB':
                    locations[i].set_location_as_hub()
                    Truck.hub_location = locations[i]
                    locations[i].hub_distance = 0
                    locations[i].been_assigned = True
                zip_match = re.search(r'\((\d+)\)', address_zip_rows[i])
                if zip_match:
                    zip_code = int(zip_match.group(1))
                    location = locations[i]
                    if not location.zip_code and name == location.name:
                        location.set_zip_code(zip_code)

                distance_dict = {}
                for j in range(0, i):
                    distance_dict[locations[j]] = float(distances_rows[i][j])
                for k in range(i + 1, len(distances_rows)):
                    distance_dict[locations[k]] = float(distances_rows[k][i])

                locations[i].set_distance_dict(distance_dict)
                if not locations[i].is_hub:
                    locations[i].hub_distance = locations[i].distance_dict[Truck.hub_location]
        return tuple(locations)

    @staticmethod
    def initialize_packages(locations: Tuple[Location], filepath=config.PACKAGE_CSV_FILE) -> Tuple[Package]:
        """
        Initializes and returns a list of Package objects based on the data from a CSV file
            and the provided set of Location objects.

        Args:
            locations (Set[Location]): The set of Location objects used for package initialization.
            filepath (str): The filepath of the CSV file containing package data.

        Returns:
            Tuple[Package]: The tuple of Package objects initialized from the CSV file.

        Time Complexity: O(n * m)
        Space Complexity: O(n + m)
        """

        packages = []
        with open(filepath, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                row: dict = row
                package_id = int(row['Package ID'])
                address: str = row['Address'].strip()
                city = UtahCity[row['City'].replace(' ', '_').upper()]
                zip_code = int(row['Zip'].strip())
                package_location = None
                for location in locations:
                    if location.address == address and location.zip_code == zip_code:
                        package_location = location
                        package_location.city = city
                        if not location.state:
                            location.state = package_location.city.state
                        break
                if not package_location:
                    raise ImportError
                deadline = config.DELIVERY_RETURN_TIME if row['Delivery Deadline'] == 'EOD' else \
                    datetime.strptime(row['Delivery Deadline'], '%I:%M:%S %p').time()
                weight = int(row['Mass KILO'])
                special_note = row['Special Notes']
                is_verified_address = not special_note.startswith('Wrong address')
                if not is_verified_address:
                    location.has_unconfirmed_package = True
                package = Package(package_id=package_id, location=package_location,
                                  is_verified_address=is_verified_address, deadline=deadline,
                                  weight=weight, special_note=special_note)
                _set_arrival_time(package)
                _set_earliest_location_deadline(package.location, package.deadline)
                _set_latest_location_package_arrival(package.location, package.hub_arrival_time)
                _set_assigned_truck(package)
                _set_bundled_packages_ids(package)
                packages.append(package)
                package.location.package_set.add(package)
            _set_bundled_packages(packages)
        return tuple(packages)
