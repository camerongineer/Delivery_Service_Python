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


# def _nearest_neighbors(truck: Truck, in_location_package_dict: dict):
#     sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
#     undeliverable_locations = get_undeliverable_locations(truck, PackageHandler.all_packages)
#     for location, distance in sorted_location_dict:
#         if location.is_hub or location in undeliverable_locations:
#             continue
#         if location in in_location_package_dict.keys() and not location.been_routed:
#             out_packages = in_location_package_dict[location]
#             if not _is_deliverable_package_set(out_packages):
#                 continue
#             else:
#                 return out_packages
#     return None


def _nearest_neighbors(truck: Truck, in_location_package_dict: dict):
    sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
    undeliverable_locations = get_undeliverable_locations(truck, PackageHandler.all_packages)
    for location, distance in sorted_location_dict:
        if location.is_hub or location in undeliverable_locations:
            continue
        if location in in_location_package_dict.keys() and not location.been_routed:
            out_packages = in_location_package_dict[location]
            for first_location, other_distance in sorted_location_dict:
                if first_location.is_hub and not first_location.been_routed and location is not first_location:
                    continue
                for second_location, second_distance in sorted_location_dict:
                    if second_location.is_hub and not second_location.been_routed and location is not second_location:
                        if truck.current_location.distance_dict[first_location] + first_location.distance_dict[second_location] <= distance + .5:
                            print('BETTER!')
            if not _is_deliverable_package_set(out_packages):
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
    if not in_packages:
        return False
    for in_package in in_packages:
        if not in_package.is_verified_address or in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def _is_loadable_package_set(in_packages: List[Package]):
    for in_package in in_packages:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
    return True


def get_undeliverable_locations(truck: Truck, in_packages: Set[Package]):
    undeliverable_locations = set()
    for package in in_packages:
        if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (
                package.assigned_truck_id and package.assigned_truck_id != truck.truck_id):
            undeliverable_locations.add(package.location)
    return undeliverable_locations


def _in_close_proximity_of_undeliverable(truck: Truck, in_location: Location, in_packages: Set[Package]) -> bool:
    undeliverable_locations = get_undeliverable_locations(truck, in_packages)
    for location in undeliverable_locations:
        if location is in_location or location.distance_dict[in_location] < 1:
            return True
    return False


def _travel_to_next_location(truck: Truck):
    _increment_drive_miles(truck)
    truck.previous_location = truck.current_location
    truck.current_location = truck.next_location
    truck.current_location.been_routed = True
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
    return (truck.distance(to_hub=True) + truck.distance(origin_location=truck.hub_location)) <= (
            truck.distance() * 1.5)


def _should_return_to_hub(truck: Truck, package_total_at_next_location: int, undelivered_total: int) -> bool:
    return len(truck) + undelivered_total > config.NUM_TRUCK_CAPACITY and \
        (len(truck) + package_total_at_next_location > config.NUM_TRUCK_CAPACITY or
         (_short_detour_to_hub(truck) and len(truck) > 12) or
         (truck.distance(to_hub=True) < 2.0 and len(truck) > 8))
    # truck.current_location.earliest_deadline == time(hour=9) or\


class RouteBuilder:
    @staticmethod
    def get_optimized_route(truck: Truck, in_location_package_dict: dict = PackageHandler.all_packages,
                            route_start_time=config.DELIVERY_DISPATCH_TIME):
        truck.set_clock(route_start_time)
        PackageHandler.bulk_status_update(truck.clock)
        next_package_set = _nearest_neighbors(truck, in_location_package_dict)
        total_packages = sum(len(packages) for packages in in_location_package_dict.values())
        while next_package_set:
            total_packages -= len(next_package_set)
            truck.next_location = list(next_package_set)[0].location
            print(truck)
            if _should_return_to_hub(truck, len(next_package_set), total_packages):
                _return_to_hub(truck)
                truck.unload()
                print('\nReturned to hub to reload')
                PackageHandler.bulk_status_update(truck.clock)
                next_package_set = _nearest_neighbors(truck, in_location_package_dict)
                continue
            truck.record()
            truck.add_all_packages(next_package_set)
            _travel_to_next_location(truck)
            PackageHandler.bulk_status_update(truck.clock)
            next_package_set = _nearest_neighbors(truck, in_location_package_dict)
        truck.completion_time = truck.clock

    @staticmethod
    def get_routed_locations(in_packages: Set[Package] = None) -> Set[Location]:
        routed_locations = set([location for location in PackageHandler.all_locations if location.been_routed])
        if in_packages:
            routed_locations = set([package.location for package in in_packages if package.location.been_routed])
        return routed_locations
