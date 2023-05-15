import operator
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

def _better_solution(nearest: Location, truck: Truck, in_location_package_dict: dict):
    sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
    sorted_nearest_location_dict = sorted(nearest.distance_dict.items(), key=lambda _location: _location[1])
    closest_to_nearest = None
    for location_from_nearest, mileage_from_nearest in sorted_nearest_location_dict:
        if not location_from_nearest.is_hub and location_from_nearest is not truck.current_location:
            nearest_package_set = in_location_package_dict[location_from_nearest]
            if _is_deliverable_package_set(nearest_package_set):
                closest_to_nearest = location_from_nearest
                break
    if not closest_to_nearest:
        return
    time_delta = 3600
    sum_of_nearest_close_deadlines = len([location for location in [nearest, closest_to_nearest] if
                                          location.has_close_deadline(truck.clock, time_delta=time_delta)])
    better_solutions = dict()
    for first_location, other_distance in sorted_location_dict:
        if first_location.is_hub or first_location.been_routed or nearest is first_location or _in_close_proximity_of_undeliverable(
                truck, first_location):
            continue
        for second_location, second_distance in sorted_location_dict:
            if second_location.is_hub or second_location.been_routed or nearest is second_location or first_location is second_location or _in_close_proximity_of_undeliverable(
                    truck, second_location):
                continue
            total_distance = truck.current_location.distance_dict[first_location] + first_location.distance_dict[
                second_location]
            total_mileage_from_nearest = truck.current_location.distance_dict[nearest] + nearest.distance_dict[
                closest_to_nearest]
            first_packages = in_location_package_dict[first_location]
            second_packages = in_location_package_dict[second_location]
            estimated_package_total = len(first_packages) + len(second_packages) + len(truck)
            sum_of_better_solution_close_deadlines = len([location for location in [first_location, second_location] if
                                                          location.has_close_deadline(truck.clock,
                                                                                      time_delta=time_delta)])
            if estimated_package_total > config.NUM_TRUCK_CAPACITY or sum_of_better_solution_close_deadlines < sum_of_nearest_close_deadlines:
                print('Heading to close_deadline')
                return
            if estimated_package_total > config.NUM_TRUCK_CAPACITY / 2:
                total_distance += second_location.distance_dict[Truck.hub_location]
                total_mileage_from_nearest += closest_to_nearest.distance_dict[Truck.hub_location]
            if total_distance <= total_mileage_from_nearest:

                if _is_deliverable_package_set(first_packages) and _is_deliverable_package_set(second_packages):
                    better_solutions[total_distance] = (first_packages, second_packages)
                    print(
                        f'{truck.current_location.name} to {nearest.name} is {total_mileage_from_nearest} then from {nearest.name} to {closest_to_nearest.name} is {nearest.distance_dict[closest_to_nearest]} totaling {total_mileage_from_nearest}')
                    print(
                        f'{truck.current_location.name} to {first_location.name} is {truck.current_location.distance_dict[first_location]} then from {first_location.name} to {second_location.name} is {second_location.distance_dict[first_location]} totaling {total_distance}\n\n')
                    print(sum_of_nearest_close_deadlines, sum_of_better_solution_close_deadlines)
    return better_solutions


def _nearest_neighbors(truck: Truck, in_location_package_dict: dict):
    sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
    undeliverable_locations = get_undeliverable_locations(truck)
    for location, distance in sorted_location_dict:
        if location.is_hub or location in undeliverable_locations:
            continue
        if location in in_location_package_dict.keys() and not location.been_routed:
            out_packages = in_location_package_dict[location]
            if not _is_deliverable_package_set(out_packages):
                continue
            else:
                better_solutions = _better_solution(location, truck, in_location_package_dict)
                if better_solutions:
                    sorted_better_solutions_mileage = sorted(better_solutions.keys())
                    for mileage in sorted_better_solutions_mileage:
                        package_total = sum(len(packages) for packages in better_solutions[mileage])
                        if package_total + len(truck) <= config.NUM_TRUCK_CAPACITY:
                            if not _is_deliverable_package_set(better_solutions[sorted_better_solutions_mileage[0]][0]):
                                continue
                            return better_solutions[sorted_better_solutions_mileage[0]][0]
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


def get_undeliverable_locations(truck: Truck):
    undeliverable_locations = set()
    location_package_dict = PackageHandler.get_location_package_dict()
    for location, packages in location_package_dict.items():
        for package in packages:
            if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (
                    package.assigned_truck_id and package.assigned_truck_id != truck.truck_id):
                undeliverable_locations.add(location)
    return undeliverable_locations


def _in_close_proximity_of_undeliverable(truck: Truck, in_location: Location) -> bool:
    undeliverable_locations = get_undeliverable_locations(truck)
    for location in undeliverable_locations:
        if location is in_location or location.distance_dict[in_location] < 1:
            return True
    return False


def _in_close_proximity_to_dispatched_partner(truck: Truck):
    return truck.partner.is_dispatched and not truck.partner.current_location.is_hub and \
        truck.partner.distance(to_hub=True) > truck.distance(target_location=truck.partner.current_location)


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
    expected_status_update_times = PackageHandler.get_all_expected_status_update_times(
        special_times=PackageHandler.today_special_times, start_time=truck.clock)
    while truck.mileage <= destination_mileage:
        truck.set_clock(TimeConversion.convert_miles_to_time(
            miles=truck.mileage,
            start_time=truck.dispatch_time,
            pause_seconds=TimeConversion.get_paused_seconds(truck.pause_ledger, truck.clock)))
        if truck.clock in expected_status_update_times:
            PackageHandler.bulk_status_update(truck.clock)
            for package in PackageHandler.get_all_late_packages(truck.clock):
                print('LATE', package)
        while truck.is_paused(truck.clock):
            truck.set_clock(TimeConversion.increment_time(truck.clock))
            if truck.clock in expected_status_update_times:
                PackageHandler.bulk_status_update(truck.clock)
        truck.drive()


def _short_detour_to_hub(truck: Truck):
    if truck.current_location.is_hub:
        return False
    return (truck.distance(to_hub=True) + truck.distance(origin_location=truck.hub_location)) <= (
            truck.distance() * 1.1)


def _should_return_to_hub(truck: Truck, package_total_at_next_location: int, undelivered_total: int) -> bool:
    return len(truck) + undelivered_total > config.NUM_TRUCK_CAPACITY and \
        (len(truck) + package_total_at_next_location > config.NUM_TRUCK_CAPACITY or
         (_short_detour_to_hub(truck) and len(truck) > 3) or
         (truck.distance(to_hub=True) < 2.0 and len(truck) > 8))

def _should_pause_for_delayed_packages(truck: Truck):
    if truck.current_location.is_hub and not PackageHandler.get_deadline_packages(ignore_routed=True) and PackageHandler.get_delayed_packages(ignore_arrived=True):
        print('YES')


def _all_deadlines_met(target_time: time) -> bool:
    return not PackageHandler.get_deadline_packages(target_time)


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
                if _should_pause_for_delayed_packages(truck):
                    _return_to_hub(truck, pause_end_at_hub=time(hour=9, minute=5))
                else:
                    _return_to_hub(truck, pause_end_at_hub=time(hour=9, minute=5))
                truck.unload()
                print('\nReturned to hub to reload')
                PackageHandler.bulk_status_update(truck.clock)
                next_package_set = _nearest_neighbors(truck, in_location_package_dict)
                continue
            truck.record()
            _should_pause_for_delayed_packages(truck)
            truck.add_all_packages(next_package_set)
            _travel_to_next_location(truck)
            PackageHandler.bulk_status_update(truck.clock)
            next_package_set = _nearest_neighbors(truck, in_location_package_dict)
        truck.completion_time = truck.clock

    # @staticmethod
    # def get_optimized_route(truck: Truck, in_location_package_dict: dict = PackageHandler.all_packages,
    #                         route_start_time=config.DELIVERY_DISPATCH_TIME):
    #     truck.set_clock(route_start_time)
    #     PackageHandler.bulk_status_update(truck.clock)
    #     next_package_set = _nearest_neighbors(truck, in_location_package_dict)
    #     total_packages = sum(len(packages) for packages in in_location_package_dict.values())
    #     while next_package_set:
    #         total_packages -= len(next_package_set)
    #         truck.next_location = list(next_package_set)[0].location
    #         print(truck)
    #         if _should_return_to_hub(truck, len(next_package_set), total_packages):
    #             _return_to_hub(truck)
    #             truck.unload()
    #             print('\nReturned to hub to reload')
    #             PackageHandler.bulk_status_update(truck.clock)
    #             next_package_set = _nearest_neighbors(truck, in_location_package_dict)
    #             continue
    #         truck.record()
    #         truck.add_all_packages(next_package_set)
    #         _travel_to_next_location(truck)
    #         PackageHandler.bulk_status_update(truck.clock)
    #         next_package_set = _nearest_neighbors(truck, in_location_package_dict)
    #     truck.completion_time = truck.clock
    #
    @staticmethod
    def get_routed_locations(in_packages: Set[Package] = None) -> Set[Location]:
        routed_locations = set([location for location in PackageHandler.all_locations if location.been_routed])
        if in_packages:
            routed_locations = set([package.location for package in in_packages if package.location.been_routed])
        return routed_locations
