import re
from datetime import time
from typing import List, Set

__all__ = ['PackageHandler']

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash
from src.utilities.time_conversion import TimeConversion


def _is_loadable_package_set(truck: Truck, in_package_set: Set[Package]) -> bool:
    for in_package in in_package_set:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
        if in_package.assigned_truck_id and in_package.assigned_truck_id != truck.truck_id:
            return False
    return True


def _is_package_arriving_at_hub(package: Package, current_time: time) -> bool:
    return package.status is DeliveryStatus.ON_ROUTE_TO_DEPOT and \
        TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time)


def _is_package_address_updating(package: Package, current_time: time) -> bool:
    return TimeConversion.is_time_at_or_before_other_time(config.PACKAGE_9_ADDRESS_CHANGE_TIME, current_time) and \
        not package.is_verified_address


class PackageHandler:
    all_locations = CsvParser.initialize_locations()
    all_packages = CsvParser.initialize_packages(all_locations)
    package_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
    package_hash.add_all_packages(all_packages)
    Truck.hub_location = [location for location in all_locations if location.is_hub][0]

    @staticmethod
    def load_packages(truck: Truck, package_sets: List[Set[Package]]):
        for package_set in package_sets:
            if truck.current_location is not Truck.hub_location or not _is_loadable_package_set(truck, package_set):
                return False
        for package_set in package_sets:
            for package in package_set:
                package.update_status(DeliveryStatus.LOADED, truck.clock)
                truck.add_package(package)
            return True

    @staticmethod
    def update_delivery_location(locations_list: List[Location], package: Package, updated_address: str):
        try:
            address, city, state_zip = updated_address.split(', ')
            zip_code = int(state_zip.split(' ')[1])
            for location in locations_list:
                if str(address).startswith(location.address) and location.zip_code == zip_code:
                    package.location = location
                    package.is_verified_address = True
                    return True
        except (ValueError, TypeError):
            return False
        return False

    @staticmethod
    def bulk_status_update(current_time: time, packages=all_packages):
        for package in packages:
            if _is_package_arriving_at_hub(package, current_time):
                package.update_status(DeliveryStatus.AT_HUB, current_time)
            if _is_package_address_updating(package, current_time):
                old_location = package.location.address
                PackageHandler.update_delivery_location(PackageHandler.all_locations, package, config.PACKAGE_9_UPDATED_ADDRESS)
                new_location = package.location.address
                print(
                    f'Package: {package.package_id:02} address changed from "{old_location}" to "{new_location} at {current_time}"')

    # @staticmethod
    # def delayed_packages_arrived(in_packages: List[Package], current_time: time):
    #     latest_arrival = in_packages[0].location.latest_package_arrival
    #     if TimeConversion.is_time_at_or_before_other_time(latest_arrival, current_time):
    #         for in_package in in_packages:
    #             in_package.status = DeliveryStatus.AT_HUB

    @staticmethod
    def get_location_package_dict(packages=all_packages):
        location_package_dict = dict()
        for package in packages:
            if package.location not in location_package_dict:
                location_package_dict[package.location] = []
            location_package_dict[package.location].append(package)
        return location_package_dict

    @staticmethod
    def get_location_packages(location: Location, packages=all_packages):
        if location not in PackageHandler.get_location_package_dict(packages).keys():
            return None
        return set(PackageHandler.get_location_package_dict(packages)[location])

    @staticmethod
    def get_all_packages_at_bundled_locations(bundled_packages: List[Package], in_packages=all_packages):
        bundled_set = set()
        for package in bundled_packages:
            all_packages_at_location = PackageHandler.get_location_packages(package.location, in_packages)
            for bundled_package in all_packages_at_location:
                bundled_set.add(bundled_package)
        return bundled_set

    @staticmethod
    def is_delivered_on_time(current_time: time, packages: Set[Package]):
        for package in packages:
            if not TimeConversion.is_time_at_or_before_other_time(current_time, package.deadline):
                print(f'Package id{package.package_id} was delivered late at {current_time}')

    @staticmethod
    def get_bundled_package_ids(packages: List[Package]):
        return PackageHandler.get_special_note_bundles('Must be delivered with ', packages)

    @staticmethod
    def unionize_bundled_sets(bundled_sets):
        i = 0
        while i < len(bundled_sets):
            current_set = bundled_sets[i]
            intersecting_sets = [bundle for bundle in bundled_sets[i + 1:] if current_set.intersection(bundle)]
            if intersecting_sets:
                for intersecting_set in intersecting_sets:
                    current_set = current_set.union(intersecting_set)
                    bundled_sets.remove(intersecting_set)
                bundled_sets[i] = current_set
            i += 1

    @staticmethod
    def get_special_note_bundles(starting_pattern: str, packages=all_packages):
        bundle_map = {}
        for package in packages:
            if str(package.special_note).startswith(starting_pattern):
                special_note = package.special_note
                pattern = r'\d+'
                package_ids = [int(match) for match in re.findall(pattern, special_note)]
                bundle_map[package.package_id] = package_ids
        return bundle_map

    @staticmethod
    def get_bundled_packages(packages=all_packages) -> List[Set[Package]]:
        custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
        custom_hash.add_all_packages(packages)
        bundle_map = PackageHandler.get_bundled_package_ids(packages)
        package_bundle_sets = []
        for package_id in bundle_map.keys():
            bundle_set = set()
            bundle_set.add(custom_hash.get_package(package_id))
            for bundled_package_id in bundle_map[package_id]:
                bundle_set.add(custom_hash.get_package(bundled_package_id))
            package_bundle_sets.append(bundle_set)
        PackageHandler.unionize_bundled_sets(package_bundle_sets)
        return package_bundle_sets

    @staticmethod
    def get_delayed_packages(packages=all_packages) -> Set[Package]:
        delayed_packages = set()
        for package in packages:
            if package.hub_arrival_time > config.DELIVERY_DISPATCH_TIME:
                delayed_packages.add(package)
        return delayed_packages

    @staticmethod
    def get_assigned_truck_packages(truck_id: int, packages=all_packages):
        truck_map = PackageHandler.get_special_note_bundles('Can only be on truck ', packages)
        truck_packages = set()
        for package in packages:
            if package.package_id in truck_map.keys():
                if truck_map[package.package_id].pop() == truck_id:
                    truck_packages.add(package)
        return truck_packages

    @staticmethod
    def subtract_package_set(packages_to_remove: Set[Package], original_packages_set: Set[Package]):
        for package in original_packages_set:
            if package in packages_to_remove:
                original_packages_set.remove(package)


