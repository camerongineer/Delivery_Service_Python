from datetime import time
from typing import List, Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion

__all__ = ['RouteBuilder']


def _nearest_neighbors(truck: Truck, in_packages: List[Package]):
    sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
    undeliverable_locations = get_undeliverable_locations(truck)
    for location, distance in sorted_location_dict:
        if location.is_hub or location in undeliverable_locations:
            continue
        if not location.been_routed:
            out_packages = PackageHandler.get_location_packages(location, in_packages)
            if not _is_deliverable_package_set(out_packages) or _in_close_proximity_of_undeliverable(truck, location):
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


def _is_location_in_package_set(in_location: Location, in_packages: List[Package]) -> bool:
    for in_package in in_packages:
        if in_package.location == in_location:
            return True
    return False


def _is_deliverable_package_set(in_packages: Set[Package]):
    for in_package in in_packages:
        if not in_package.is_verified_address or in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def _is_loadable_package_set(in_packages: List[Package]):
    for in_package in in_packages:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def get_undeliverable_locations(truck: Truck):
    undeliverable_locations = set()
    for package in PackageHandler.all_packages:
        if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (package.assigned_truck_id and package.assigned_truck_id != truck.truck_id):
            undeliverable_locations.add(package.location)
    return undeliverable_locations


def _in_close_proximity_of_undeliverable(truck: Truck, in_location: Location):
    undeliverable_locations = get_undeliverable_locations(truck)
    for location in undeliverable_locations:
        if location is in_location or location.distance_dict[in_location] < 1:
            return True
    return False


def _travel_to_next_location(truck: Truck):
    _increment_drive_miles(truck)
    truck.previous_location = truck.current_location
    truck.current_location = truck.next_location
    truck.next_location = None


def _return_to_hub(truck: Truck, pause_end_at_hub=None):
    truck.next_location = truck.hub_location
    truck.record()
    _increment_drive_miles(truck)
    if pause_end_at_hub:
        truck.pause(truck.clock, pause_end_at_hub)
    truck.previous_location = truck.current_location
    truck.current_location = truck.hub_location


def _increment_drive_miles(truck: Truck):
    miles_to_next = truck.current_location.distance_dict[truck.next_location]
    destination_mileage = truck.mileage + miles_to_next
    while truck.mileage <= destination_mileage:
        truck.set_clock(TimeConversion.convert_miles_to_time(
            miles=truck.mileage,
            start_time=truck.dispatch_time,
            pause_seconds=TimeConversion.get_paused_seconds(truck.pause_ledger, truck.clock)))
        while truck.is_paused(truck.clock):
            truck.set_clock(TimeConversion.increment_time(truck.clock))
        truck.drive()


def _short_detour_to_hub(truck: Truck):
    if truck.current_location.is_hub:
        return False
    return (truck.distance(to_hub=True) + truck.distance(origin_location=truck.hub_location)) <= (truck.distance() * 1.5)

class RouteBuilder:
    @staticmethod
    def get_optimized_route(truck: Truck, packages: List[Package] = PackageHandler.all_packages, route_start_time=config.DELIVERY_DISPATCH_TIME):
        truck.set_clock(route_start_time)
        next_packages = _nearest_neighbors(truck, packages)
        package_count = 0
        total_packages = len(packages)
        while next_packages:
            if PackageHandler.get_location_packages(truck.current_location, packages):
                print(len(PackageHandler.get_location_packages(truck.current_location, packages)), ' Packages Delivered')
            truck.current_location.been_routed = True
            package_count += len(next_packages)
            total_packages -= len(next_packages)
            truck.next_location = list(next_packages)[0].location
            if package_count > config.NUM_TRUCK_CAPACITY or truck.current_location.earliest_deadline == time(hour=9) or (_short_detour_to_hub(truck) and package_count > 6):
                _return_to_hub(truck)
                package_count = 0
                print('Reloading')
                PackageHandler.bulk_status_update(truck.clock, packages)
                next_packages = _nearest_neighbors(truck, packages)
                continue
            truck.record()
            _travel_to_next_location(truck)
            PackageHandler.bulk_status_update(truck.clock, packages)
            next_packages = _nearest_neighbors(truck, packages)
        truck.completion_time = truck.clock
