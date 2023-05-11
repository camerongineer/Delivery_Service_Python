from datetime import time
from typing import List, Set
import re



__all__ = ['RouteBuilder']

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion

all_locations = CsvParser.initialize_locations()
all_packages = CsvParser.initialize_packages(all_locations)
package_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
package_hash.add_all_packages(all_packages)

Truck.hub_location = [location for location in all_locations if location.is_hub][0]


def _nearest_neighbors(in_location: Location, in_packages: List[Package], current_time: time):
    sorted_location_dict = sorted(in_location.distance_dict.items(), key=lambda _location: _location[1])
    for location, distance in sorted_location_dict:
        if location.is_hub:
            continue
        if not location.been_routed:
            out_packages = RouteBuilder.get_location_packages(location, in_packages)
            if not is_deliverable_package_set(out_packages):
                continue
            else:
                return out_packages
    return None


def _miles_from_other_location(origin_location: Location, other_location: Location):
    if origin_location is other_location:
        return 0
    return origin_location.distance_dict[other_location]


def _time_to_other_location(origin_location: Location, other_location: Location):
    miles_to_other_location = _miles_from_other_location(origin_location, other_location)
    return miles_to_other_location / config.DELIVERY_TRUCK_MPH

def _arrival_time_at_next_location(origin_location: Location, next_location: Location):
    pass

def is_location_in_package_set(in_location: Location, in_packages: List[Package]) -> bool:
    for in_package in in_packages:
        if in_package.location == in_location:
            return True
    return False


def is_deliverable_package_set(in_packages: Set[Package]):
    for in_package in in_packages:
        if not in_package.is_verified_address or in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def is_loadable_package_set(in_packages: List[Package]):
    for in_package in in_packages:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def _get_bundled_package_ids(packages: List[Package]):
    return _get_special_note_bundles(packages, 'Must be delivered with ')


def _unionize_bundled_sets(bundled_sets):
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


def _get_special_note_bundles(packages: List[Package], starting_pattern: str):
    bundle_map = {}
    for package in packages:
        if str(package.special_note).startswith(starting_pattern):
            special_note = package.special_note
            pattern = r'\d+'
            package_ids = [int(match) for match in re.findall(pattern, special_note)]
            bundle_map[package.package_id] = package_ids
    return bundle_map


class RouteBuilder:
    @staticmethod
    def get_optimized_route(truck: Truck, packages: List[Package] = all_packages):
        truck.dispatch_time = config.DELIVERY_DISPATCH_TIME
        PackageHandler.bulk_status_update(truck.dispatch_time, DeliveryStatus.AT_HUB, all_packages)
        current_location = Truck.hub_location
        travel_ledger = dict()
        total_miles = 0.0
        current_time = truck.dispatch_time
        next_packages = _nearest_neighbors(Truck.hub_location, packages, current_time)
        while next_packages:
            next_location = list(next_packages)[0].location
            miles_to_next = current_location.distance_dict[next_location]
            current_drive_miles = 0.0
            while current_drive_miles <= miles_to_next:
                current_time = TimeConversion.convert_miles_to_time(total_miles + current_drive_miles, truck.dispatch_time, pause_seconds=truck._total_paused_seconds(current_time))
                while truck.is_paused(current_time):
                    current_time = TimeConversion.increment_time(current_time)
                current_drive_miles += 0.1
            total_miles += miles_to_next
            travel_ledger[total_miles] = (current_time, current_location, next_location)
            current_location = next_location
            current_location.been_routed = True
            PackageHandler.bulk_status_update(current_time, DeliveryStatus.AT_HUB, list(all_packages))
            next_packages = _nearest_neighbors(current_location, packages, current_time)
        truck.set_travel_ledger(travel_ledger)

    @staticmethod
    def get_most_spread_out_stops(packages: List[Package]):
        pass

    @staticmethod
    def get_location_packages(location: Location, packages: List[Package]):
        return set(RouteBuilder.get_location_package_dict(packages)[location])

    @staticmethod
    def get_all_packages_at_bundled_locations(bundled_packages: List[Package], all_packages: List[Package]):
        bundled_set = set()
        for package in bundled_packages:
            all_packages_at_location = RouteBuilder.get_location_packages(package.location, all_packages)
            for bundled_package in all_packages_at_location:
                bundled_set.add(bundled_package)
        return bundled_set

    @staticmethod
    def get_location_package_dict(packages: List[Package]):
        location_package_dict = dict()
        for package in packages:
            if package.location not in location_package_dict:
                location_package_dict[package.location] = []
            location_package_dict[package.location].append(package)
        return location_package_dict

    @staticmethod
    def get_bundled_packages(packages: List[Package]) -> List[Set[Package]]:
        from src.config import NUM_TRUCK_CAPACITY
        custom_hash = CustomHash(NUM_TRUCK_CAPACITY)
        custom_hash.add_all_packages(packages)
        bundle_map = _get_bundled_package_ids(packages)
        package_bundle_sets = []
        for package_id in bundle_map.keys():
            bundle_set = set()
            bundle_set.add(custom_hash.get_package(package_id))
            for bundled_package_id in bundle_map[package_id]:
                bundle_set.add(custom_hash.get_package(bundled_package_id))
            package_bundle_sets.append(bundle_set)
        _unionize_bundled_sets(package_bundle_sets)
        return package_bundle_sets

    @staticmethod
    def get_delayed_packages(packages: List[Package]) -> Set[Package]:
        from src.config import DELIVERY_DISPATCH_TIME
        delayed_packages = set()
        for package in packages:
            if package.hub_arrival_time > DELIVERY_DISPATCH_TIME:
                delayed_packages.add(package)
        return delayed_packages

    @staticmethod
    def get_assigned_truck_packages(packages: List[Package], truck_id: int):
        truck_map = _get_special_note_bundles(packages, 'Can only be on truck ')
        truck_packages = set()
        for package in packages:
            if package.package_id in truck_map.keys():
                if truck_map[package.package_id].pop() == truck_id:
                    truck_packages.add(package)
        return truck_packages
