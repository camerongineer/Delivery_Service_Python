# import operator
# from datetime import time
# from typing import List, Set
#
# from src import config
# from src.constants.delivery_status import DeliveryStatus
# from src.exceptions.route_builder_error import InvalidRouteRunError
# from src.models.location import Location
# from src.models.package import Package
# from src.models.truck import Truck
# from src.utilities.package_handler import PackageHandler
# from src.utilities.time_conversion import TimeConversion
#
# __all__ = ['RouteBuilder']
#
#
# # def _nearest_neighbors(truck: Truck, in_location_package_dict: dict):
# #     sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
# #     undeliverable_locations = get_undeliverable_locations(truck, PackageHandler.all_packages)
# #     for location, distance in sorted_location_dict:
# #         if location.is_hub or location in undeliverable_locations:
# #             continue
# #         if location in in_location_package_dict.keys() and not location.been_routed:
# #             out_packages = in_location_package_dict[location]
# #             if not _is_deliverable_package_set(out_packages):
# #                 continue
# #             else:
# #                 return out_packages
# #     return None
#
# def _better_solution(nearest: Location, truck: Truck, in_location_package_dict: dict):
#     sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
#     sorted_nearest_location_dict = sorted(nearest.distance_dict.items(), key=lambda _location: _location[1])
#     closest_to_nearest = None
#
#     for location_from_nearest, mileage_from_nearest in sorted_nearest_location_dict:
#         if not location_from_nearest.is_hub and location_from_nearest is not truck.current_location:
#             nearest_package_set = in_location_package_dict[location_from_nearest]
#             if _is_deliverable_package_set(nearest_package_set):
#                 closest_to_nearest = location_from_nearest
#                 break
#     if not closest_to_nearest:
#         return
#     time_delta = 5400
#     sum_of_nearest_close_deadlines = len([location for location in [nearest, closest_to_nearest] if
#                                           location.has_close_deadline(truck.clock, time_delta=time_delta)])
#     better_solutions = dict()
#     for first_location, other_distance in sorted_location_dict:
#         if first_location.is_hub or first_location.been_routed or nearest is first_location or _in_close_proximity_of_undeliverable(
#                 truck, first_location):
#             continue
#         for second_location, second_distance in sorted_location_dict:
#             if second_location.is_hub or second_location.been_routed or nearest is second_location or first_location is second_location or _in_close_proximity_of_undeliverable(
#                     truck, second_location):
#                 continue
#             total_distance = truck.current_location.distance_dict[first_location] + first_location.distance_dict[
#                 second_location]
#             total_mileage_from_nearest = truck.current_location.distance_dict[nearest] + nearest.distance_dict[
#                 closest_to_nearest]
#             first_packages = in_location_package_dict[first_location]
#             second_packages = in_location_package_dict[second_location]
#             estimated_package_total = len(first_packages) + len(second_packages) + len(truck)
#             sum_of_better_solution_close_deadlines = len([location for location in [first_location, second_location] if
#                                                           location.has_close_deadline(truck.clock,
#                                                                                       time_delta=time_delta)])
#             if sum_of_better_solution_close_deadlines < sum_of_nearest_close_deadlines:
#                 return
#             if estimated_package_total > config.NUM_TRUCK_CAPACITY / 2:
#                 total_distance += second_location.distance_dict[Truck.hub_location]
#                 total_mileage_from_nearest += closest_to_nearest.distance_dict[Truck.hub_location]
#             if total_distance <= total_mileage_from_nearest:
#
#                 if _is_deliverable_package_set(first_packages) and _is_deliverable_package_set(second_packages):
#                     better_solutions[total_distance] = (first_packages, second_packages)
#                     print(
#                         f'{truck.current_location.name} to {nearest.name} is {total_mileage_from_nearest} then from {nearest.name} to {closest_to_nearest.name} is {nearest.distance_dict[closest_to_nearest]} totaling {total_mileage_from_nearest}')
#                     print(
#                         f'{truck.current_location.name} to {first_location.name} is {truck.current_location.distance_dict[first_location]} then from {first_location.name} to {second_location.name} is {second_location.distance_dict[first_location]} totaling {total_distance}\n\n')
#                     print(sum_of_nearest_close_deadlines, sum_of_better_solution_close_deadlines)
#     return better_solutions
#
#
# def _nearest_neighbors(truck: Truck, in_location_package_dict: dict):
#     sorted_location_dict = sorted(truck.current_location.distance_dict.items(), key=lambda _location: _location[1])
#     undeliverable_locations = get_undeliverable_locations(truck)
#     for location, distance in sorted_location_dict:
#         if location.is_hub or location in undeliverable_locations:
#             continue
#         if location in in_location_package_dict.keys() and not location.been_routed:
#             out_packages = in_location_package_dict[location]
#             if not _is_deliverable_package_set(out_packages):
#                 continue
#             else:
#                 better_solutions = _better_solution(location, truck, in_location_package_dict)
#                 if better_solutions:
#                     sorted_better_solutions_mileage = sorted(better_solutions.keys())
#                     for mileage in sorted_better_solutions_mileage:
#                         package_total = sum(len(packages) for packages in better_solutions[mileage])
#                         if package_total + len(truck) <= config.NUM_TRUCK_CAPACITY:
#                             if not _is_deliverable_package_set(better_solutions[sorted_better_solutions_mileage[0]][0]):
#                                 continue
#                             return better_solutions[sorted_better_solutions_mileage[0]][0]
#                 return out_packages
#     return None
#
#
# # def _two_opt(truck: Truck):
# #     valid_options = dict()
# #     for first_location, first_distance in truck.current_location.distance_dict.items():
# #         if not _is_valid_option(truck, first_location):
# #             continue
# #         for second_location, second_distance in truck.current_location.distance_dict.items():
# #             if _is_valid_option(truck, second_location, first_location):
# #                 miles_to_second = (truck.distance(target_location=first_location) +
# #                                    first_location.distance_dict[second_location])
# #                 first_location_package_total = len(PackageHandler.get_location_packages(first_location))
# #                 second_location_package_total = len(PackageHandler.get_location_packages(second_location))
# #                 if len(truck) + first_location_package_total + second_location_package_total >= config.NUM_TRUCK_CAPACITY * .6:
# #                     miles_to_second += second_location.distance_dict[truck.hub_location]
# #                 valid_options[first_location] = (miles_to_second, second_location)
# #     return _best_option(truck, valid_options)
#
# def _two_opt(truck: Truck, route_run_locations: Set[Location], is_return_run: bool, is_early_return_run: bool):
#     valid_options = dict()
#     for first_location, first_distance in truck.current_location.distance_dict.items():
#         if not _is_valid_option(truck, first_location):
#             continue
#         for second_location, second_distance in truck.current_location.distance_dict.items():
#             if _is_valid_option(truck, second_location, first_location):
#                 miles_to_second = (truck.distance(target_location=first_location) +
#                                    first_location.distance_dict[second_location])
#                 first_location_package_total = len(PackageHandler.get_location_packages(first_location))
#                 second_location_package_total = len(PackageHandler.get_location_packages(second_location))
#                 if len(truck) + first_location_package_total + second_location_package_total >= config.NUM_TRUCK_CAPACITY * .6:
#                     miles_to_second += second_location.distance_dict[truck.hub_location]
#                 valid_options[first_location] = (miles_to_second, second_location)
#     return _best_option(truck, valid_options)
#
#
# def _is_valid_option(truck: Truck, location: Location, other_location=None) -> bool:
#     return not location.is_hub and not location.been_routed and location is not other_location and \
#         not _in_close_proximity_of_undeliverable(truck, location)
#
#
# def _best_option(truck: Truck, valid_options: dict):
#     sorted_valid_options = sorted(valid_options.items(), key=lambda x: x[1][0])
#     if not valid_options:
#         return None
#     bundled_packages = PackageHandler.get_bundled_packages()
#
#     for (first_location), (total_mileage, second_location) in sorted_valid_options:
#         first_location_packages = PackageHandler.get_location_packages(first_location)
#         second_location_packages = PackageHandler.get_location_packages(second_location)
#
#         if first_location_packages.intersection(bundled_packages) and \
#                 second_location_packages.intersection(bundled_packages):
#             return first_location_packages
#
#     for first_location, (total_mileage, second_location) in sorted_valid_options:
#         first_location_packages = PackageHandler.get_location_packages(first_location)
#         if first_location_packages.intersection(bundled_packages):
#             return first_location_packages
#
#     return PackageHandler.get_location_packages(sorted_valid_options[0][0])
#
#
# def _find_furthest_opposites_from_hub():
#     locations_from_hub = sorted(Truck.hub_location.distance_dict.items(), key=lambda item: item[1], reverse=True)
#     furthest_location = locations_from_hub[0][0]
#     locations_from_furthest = sorted(furthest_location.distance_dict.items(), key=lambda item: item[1], reverse=True)
#     for i in range(len(locations_from_furthest)):
#         opposite_location = locations_from_furthest[i][0]
#         if opposite_location is Truck.hub_location:
#             continue
#         if _is_good_furthest_opposite(furthest_location, opposite_location):
#             return furthest_location, opposite_location
#
#
# def _is_good_furthest_opposite(further_location: Location, opposite_location: Location):
#     if further_location.has_required_truck_package or opposite_location.has_required_truck_package:
#         further_truck_id = PackageHandler.get_assigned_truck_id(further_location)
#         opposite_truck_id = PackageHandler.get_assigned_truck_id(opposite_location)
#         if (further_truck_id and opposite_truck_id) and further_truck_id != opposite_truck_id:
#             return False
#     bundled_locations = PackageHandler.get_package_locations(PackageHandler.get_bundled_packages())
#     if further_location in bundled_locations and opposite_location in bundled_locations:
#         return False
#     return True
#
# def _get_furthest_away_from_two_opposites(further_location: Location, opposite_location: Location):
#     max_mileage = 0
#     furthest_away = None
#     for location in PackageHandler.all_locations:
#         if location.is_hub or location is further_location or location is opposite_location:
#             continue
#         miles = further_location.distance_dict[location] + location.distance_dict[opposite_location]
#         if miles > max_mileage:
#             furthest_away = location
#     return furthest_away
#
# def _miles_from_other_location(origin_location: Location, other_location: Location):
#     if origin_location is other_location:
#         return 0
#     return origin_location.distance_dict[other_location]
#
#
# def _time_to_other_location(origin_location: Location, other_location: Location):
#     miles_to_other_location = _miles_from_other_location(origin_location, other_location)
#     return miles_to_other_location / config.DELIVERY_TRUCK_MPH
#
#
# def _is_location_in_package_set(in_location: Location, in_packages: List[Package]) -> bool:
#     for in_package in in_packages:
#         if in_package.location == in_location:
#             return True
#     return False
#
#
# def _is_deliverable_package_set(in_packages: Set[Package]):
#     if not in_packages:
#         return False
#     for in_package in in_packages:
#         if not in_package.is_verified_address or in_package.status is not DeliveryStatus.AT_HUB:
#             return False
#     return True
#
#
# def _is_loadable_package_set(in_packages: List[Package]):
#     for in_package in in_packages:
#         if in_package.status is not DeliveryStatus.AT_HUB:
#             return False
#     return True
#
#
# def get_undeliverable_locations(truck: Truck):
#     undeliverable_locations = set()
#     location_package_dict = PackageHandler.get_location_package_dict()
#     for location, packages in location_package_dict.items():
#         for package in packages:
#             if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (
#                     package.assigned_truck_id and package.assigned_truck_id != truck.truck_id):
#                 undeliverable_locations.add(location)
#     return undeliverable_locations
#
#
# def _in_close_proximity_of_undeliverable(truck: Truck, in_location: Location) -> bool:
#     undeliverable_locations = get_undeliverable_locations(truck)
#     for location in undeliverable_locations:
#         if location is in_location or location.distance_dict[in_location] < 1:
#             return True
#     return False
#
#
# def _in_close_proximity_to_dispatched_partner(truck: Truck):
#     return truck.partner.is_dispatched and not truck.partner.current_location.is_hub and \
#         truck.partner.distance(to_hub=True) > truck.distance(target_location=truck.partner.current_location)
#
#
# def _travel_to_next_location(truck: Truck):
#     _increment_drive_miles(truck)
#     truck.previous_location = truck.current_location
#     truck.current_location = truck.next_location
#     truck.current_location.been_routed = True
#     truck.next_location = None
#
#
# def _return_to_hub(truck: Truck, pause_end_at_hub=None):
#     truck.next_location = truck.hub_location
#     truck.record()
#     _increment_drive_miles(truck)
#     if pause_end_at_hub:
#         truck.pause(truck.clock, pause_end_at_hub)
#     truck.previous_location = truck.current_location
#     truck.current_location = truck.hub_location
#
#
# def _increment_drive_miles(truck: Truck):
#     miles_to_next = truck.current_location.distance_dict[truck.next_location]
#     destination_mileage = truck.mileage + miles_to_next
#     expected_status_update_times = PackageHandler.get_all_expected_status_update_times(
#         special_times=PackageHandler.today_special_times, start_time=truck.clock)
#     while truck.mileage <= destination_mileage:
#         truck.set_clock(TimeConversion.convert_miles_to_time(
#             miles=truck.mileage,
#             start_time=truck.dispatch_time,
#             pause_seconds=TimeConversion.get_paused_seconds(truck.pause_ledger, truck.clock)))
#         if truck.clock in expected_status_update_times:
#             PackageHandler.bulk_status_update(truck.clock)
#             for package in PackageHandler.get_all_late_packages(truck.clock):
#                 print('LATE', package)
#         while truck.is_paused(truck.clock):
#             truck.set_clock(TimeConversion.increment_time(truck.clock))
#             if truck.clock in expected_status_update_times:
#                 PackageHandler.bulk_status_update(truck.clock)
#         truck.drive()
#
#
# def _short_detour_to_hub(truck: Truck, multiplier: float):
#     if truck.current_location.is_hub:
#         return False
#     return (truck.distance(to_hub=True) + truck.distance(origin_location=truck.hub_location)) <= (
#             truck.distance() * multiplier)
#
#
# def _should_return_to_hub(truck: Truck, package_total_at_next_location: int, undelivered_total: int) -> bool:
#     return len(truck) + undelivered_total > config.NUM_TRUCK_CAPACITY and \
#         (len(truck) + package_total_at_next_location > config.NUM_TRUCK_CAPACITY or
#          ((_short_detour_to_hub(truck, 1.1) and len(truck) > 4) or (_short_detour_to_hub(truck, 1.5) and len(truck) > 7)) or
#          (truck.distance(to_hub=True) < 2.0 and len(truck) > 8))
#
# def _should_pause_for_delayed_packages(truck: Truck):
#     if truck.current_location.is_hub and not PackageHandler.get_deadline_packages(ignore_routed=True) and PackageHandler.get_delayed_packages(ignore_arrived=True):
#         print('YES')
#
#
# def _all_deadlines_met(target_time: time) -> bool:
#     return not PackageHandler.get_deadline_packages(target_time)
#
#
# def _get_assigned_truck_id_from_package_set(in_packages) -> int:
#     truck_id = -1
#     for package in in_packages:
#         if truck_id == -1 and package.assigned_truck_id:
#             truck_id = package.assigned_truck_id
#         elif (truck_id != -1 and package.assigned_truck_id) and truck_id != package.assigned_truck_id:
#             raise InvalidRouteRunError
#     return truck_id
#
#
# def _get_truck_id_package_tuple(in_packages):
#     return _get_assigned_truck_id_from_package_set(in_packages), in_packages
#
#
# def _get_starter_route_runs(early_return_run_locations: Set[Location]) -> dict:
#     runs = dict()
#     print(early_return_run_locations)
#     furthest, opposite = _find_furthest_opposites_from_hub()
#     furthest_between_opposites = _get_furthest_away_from_two_opposites(furthest, opposite)
#     furthest_truck_id, furthest_closest_packages = \
#         _get_truck_id_package_tuple(PackageHandler.get_closest_packages(furthest, minimum=10))
#     opposite_truck_id, opposite_closest_packages = \
#         _get_truck_id_package_tuple(PackageHandler.get_closest_packages(opposite, minimum=10))
#     furthest_between_truck_id, furthest_between_packages = \
#         _get_truck_id_package_tuple(PackageHandler.get_closest_packages(furthest_between_opposites, minimum=10))
#     if furthest_closest_packages.intersection(opposite_closest_packages):
#         if furthest_truck_id == -1 and opposite_truck_id != -1:
#             furthest_truck_id = opposite_truck_id
#         elif furthest_truck_id != -1 and opposite_truck_id == -1:
#             opposite_truck_id = furthest_truck_id
#     if furthest_truck_id in runs:
#         runs[furthest_truck_id].append(furthest_closest_packages)
#     else:
#         runs[furthest_truck_id] = [furthest_closest_packages]
#
#     if opposite_truck_id in runs:
#         runs[opposite_truck_id].append(opposite_closest_packages)
#     else:
#         runs[opposite_truck_id] = [opposite_closest_packages]
#
#     if furthest_between_truck_id in runs:
#         runs[furthest_between_truck_id].append(furthest_between_packages)
#     else:
#         runs[furthest_between_truck_id] = [furthest_between_packages]
#
#     return runs
#
# def _get_early_return_run_locations():
#     delayed_packages = PackageHandler.get_delayed_packages()
#     if not delayed_packages:
#         return None
#     latest_delay = None
#     for package in delayed_packages:
#         if not latest_delay:
#             latest_delay = package.hub_arrival_time
#         else:
#             if TimeConversion.is_time_at_or_before_other_time(latest_delay, package.hub_arrival_time):
#                 latest_delay = package.hub_arrival_time
#     early_run = set()
#     for package in PackageHandler.all_packages:
#         if TimeConversion.is_time_at_or_before_other_time(package.deadline, latest_delay):
#             early_run.add(package.location)
#     bundled_packages_locations = PackageHandler.get_package_locations(PackageHandler.get_bundled_packages())
#     if early_run.intersection(bundled_packages_locations):
#         early_run = early_run.union(bundled_packages_locations)
#     return early_run
#
# class RouteBuilder:
#     @staticmethod
#     def get_optimized_route(truck: Truck, in_location_package_dict: dict = PackageHandler.all_packages,
#                             route_start_time=config.DELIVERY_DISPATCH_TIME):
#         furthest, opposite = _find_furthest_opposites_from_hub()
#
#         print('\n\n')
#         print(RouteBuilder.build_route_runs())
#         furthest_packages = (PackageHandler.get_closest_packages(furthest, minimum=8))
#         opposite_packages = (PackageHandler.get_closest_packages(opposite, minimum=8))
#
#
#         for package in furthest_packages.intersection(PackageHandler.get_bundled_packages()):
#             print(package.location)
#         print("\n\n")
#         for package in opposite_packages.intersection(PackageHandler.get_bundled_packages()):
#             print(package.location)
#         truck.set_clock(route_start_time)
#         PackageHandler.bulk_status_update(truck.clock)
#         # next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#         next_package_set = _two_opt(truck)
#         total_packages = sum(len(packages) for packages in in_location_package_dict.values())
#         while next_package_set:
#             total_packages -= len(next_package_set)
#             truck.next_location = list(next_package_set)[0].location
#             print(truck)
#             if _should_return_to_hub(truck, len(next_package_set), total_packages):
#                 if _should_pause_for_delayed_packages(truck):
#                     _return_to_hub(truck, pause_end_at_hub=time(hour=9, minute=5))
#                 else:
#                     _return_to_hub(truck, pause_end_at_hub=time(hour=9, minute=5))
#                 truck.unload()
#                 print('\nReturned to hub to reload')
#                 PackageHandler.bulk_status_update(truck.clock)
#                 next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#                 continue
#             truck.record()
#             _should_pause_for_delayed_packages(truck)
#             truck.add_all_packages(next_package_set)
#             _travel_to_next_location(truck)
#             PackageHandler.bulk_status_update(truck.clock)
#             # next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#             next_package_set = _two_opt(truck)
#         truck.completion_time = truck.clock
#
#     @staticmethod
#     def build_optimized_route_run(truck: Truck, route_run_locations: Set[Location], is_return_run=True,
#                                   is_early_return_run=False, run_start_time=config.DELIVERY_DISPATCH_TIME):
#         truck.set_clock(run_start_time)
#         PackageHandler.bulk_status_update(truck.clock)
#         next_truck_location = _two_opt(truck, route_run_locations, is_return_run, is_early_return_run)
#         while next_truck_location is not Truck.hub_location:
#             truck.next_location = next_truck_location
#             if _should_return_to_hub(truck, route_run_locations, is_return_run, is_early_return_run):
#                 PackageHandler.bulk_status_update(truck.clock)
#                 next_truck_location = Truck.hub_location
#                 continue
#             truck.record()
#             truck.add_all_packages(PackageHandler.get_location_packages(next_truck_location))
#             _travel_to_next_location(truck)
#             PackageHandler.bulk_status_update(truck.clock)
#             next_truck_location = _two_opt(truck)
#         return truck.clock
#
#     # @staticmethod
#     # def get_optimized_route(truck: Truck, in_location_package_dict: dict = PackageHandler.all_packages,
#     #                         route_start_time=config.DELIVERY_DISPATCH_TIME):
#     #     truck.set_clock(route_start_time)
#     #     PackageHandler.bulk_status_update(truck.clock)
#     #     next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#     #     total_packages = sum(len(packages) for packages in in_location_package_dict.values())
#     #     while next_package_set:
#     #         total_packages -= len(next_package_set)
#     #         truck.next_location = list(next_package_set)[0].location
#     #         print(truck)
#     #         if _should_return_to_hub(truck, len(next_package_set), total_packages):
#     #             _return_to_hub(truck)
#     #             truck.unload()
#     #             print('\nReturned to hub to reload')
#     #             PackageHandler.bulk_status_update(truck.clock)
#     #             next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#     #             continue
#     #         truck.record()
#     #         truck.add_all_packages(next_package_set)
#     #         _travel_to_next_location(truck)
#     #         PackageHandler.bulk_status_update(truck.clock)
#     #         next_package_set = _nearest_neighbors(truck, in_location_package_dict)
#     #     truck.completion_time = truck.clock
#     #
#     @staticmethod
#     def get_routed_locations(in_packages: Set[Package] = None) -> Set[Location]:
#         routed_locations = set([location for location in PackageHandler.all_locations if location.been_routed])
#         if in_packages:
#             routed_locations = set([package.location for package in in_packages if package.location.been_routed])
#         return routed_locations
#
#     @staticmethod
#     def build_route():
#         pass
#
#     @staticmethod
#     def build_route_runs():
#         minimum_route_runs = (len(PackageHandler.all_packages) // config.NUM_TRUCK_CAPACITY) + 1
#         early_return_run_locations = _get_early_return_run_locations()
#         print(len(PackageHandler.get_all_packages_from_locations(early_return_run_locations)))
#         runs = _get_starter_route_runs(early_return_run_locations)
#         for truck_id, runs in runs.items():
#             for package_set in runs:
#                 print('Run start')
#                 delayed_stops = 0
#                 early_deadlines = 0
#                 for package in package_set:
#                     print(package.location.name, package.location.address)
#                     print(package.hub_arrival_time)
#                     print(package.deadline)
#                     if package.deadline != config.DELIVERY_RETURN_TIME:
#                         early_deadlines += 1
#                     if package.hub_arrival_time != config.STANDARD_PACKAGE_ARRIVAL_TIME:
#                         delayed_stops += 1
#                     print('\n\n')
#                 print('delays_stops:', delayed_stops)
#                 print('early_deadlines:', early_deadlines)
#         return runs
import random
from copy import copy
from typing import Set

from src import config
from src.constants.color import Color
from src.constants.run_focus import RunFocus
from src.exceptions.route_builder_error import OptimalHubReturnError, UnconfirmedPackageDeliveryError
from src.models.location import Location
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.run_planner import RunPlanner
from src.utilities.time_conversion import TimeConversion
from src.ui import UI


def _find_most_spread_out_location() -> Location:
    UI.print('Searching for location that is the most spread out from others', color=Color.YELLOW, think=True)
    most_spread_out_location = (sorted(PackageHandler.all_locations, key=lambda
        location: sum(location.distance_dict.values())).pop())
    _display_location_details(most_spread_out_location, Truck.hub_location)
    return most_spread_out_location


def _find_earliest_deadline_packages() -> Location:
    UI.print('Searching for packages with earliest deadlines', color=Color.YELLOW, think=True)
    earliest_deadlines_packages = list()
    dispatch_time = config.DELIVERY_DISPATCH_TIME
    deadline_criteria = TimeConversion.increment_time(dispatch_time, time_seconds=5400)
    for package in PackageHandler.all_packages:
        if TimeConversion.is_time_at_or_before_other_time(package.deadline, deadline_criteria):
            earliest_deadlines_packages.append(package)
    if earliest_deadlines_packages:
        earliest_deadline = sorted(earliest_deadlines_packages, key=lambda _package: _package.deadline)[0].location
        UI.print(f'Found delivery due at {earliest_deadline.earliest_deadline}', sleep_seconds=4, color=Color.RED)
        _display_location_details(earliest_deadline, Truck.hub_location)
        return earliest_deadline
    UI.print('No early_deadlines found.', color=Color.GREEN, extra_lines=1)


def _find_furthest_location_away(in_location: Location) -> Location:
    UI.print(f'Searching for location furthest away from "{in_location.name}"', color=Color.YELLOW, think=True)
    distance_sorted_locations = sorted(in_location.distance_dict.items(), key=lambda item: item[1], reverse=True)
    furthest_location = distance_sorted_locations[0][0]
    _display_location_details(furthest_location, in_location)
    return furthest_location


def _display_location_details(in_location: Location, origin_location: Location):
    package_total = len(in_location.package_set)
    UI.print(f'"{in_location.name}" at "{in_location.address}" found', 2, color=Color.BLUE)
    UI.print(f'{package_total} package' + ('s are ' if package_total != 1 else " is ") +
             'due to be delivered to this location', 2)
    UI.print(f'Approximate distance between "{origin_location.name}" at "{origin_location.address},'
             f' {origin_location.city.displayed_name}" and "{in_location.name}" at "{in_location.address},'
             f' {in_location.city.displayed_name}" is {in_location.distance(origin_location):.1f} miles',
             sleep_seconds=4, extra_lines=1)


def _analyze_best_targets(best_targets):
    targets_with_assigned_truck = [target for target in best_targets if target.has_required_truck_package]
    UI.print('Analyzing targets', think=True, extra_lines=2)
    if len(targets_with_assigned_truck) > 1:
        target_sets = {}
        for target in best_targets:
            if not target.assigned_truck_id:
                continue
            if target.assigned_truck_id in target_sets:
                target_sets[target.assigned_truck_id].add(target)
            else:
                target_sets[target.assigned_truck_id] = {target}
        if any(len(target_set) > 1 for target_set in target_sets.values()):
            truck_id = [truck_id for truck_id in target_sets.keys() if len(target_sets[truck_id]) > 1].pop()
            UI.print(f'Locations detected that are assigned to truck #{truck_id}', sleep_seconds=4, color=Color.RED)
            UI.print('Recommending these locations are assigned to the same run and also recommending all other'
                     ' locations that require this truck are also on this run if possible', think=True, extra_lines=2)
            paired_targets = [target for target in best_targets if target.assigned_truck_id == truck_id]
            remaining_targets = [target for target in best_targets if target.assigned_truck_id != truck_id]
            UI.print('Requesting backup target', think=True)
            most_spread_out_location = _find_most_spread_out_location()
            remaining_targets.append({truck_id: paired_targets})
            remaining_targets.append(most_spread_out_location)
            return remaining_targets


def _calculate_best_targets():
    best_targets = []
    package_total = len(PackageHandler.all_packages)
    truck_capacity = config.NUM_TRUCK_CAPACITY
    minimum_runs = int(package_total / config.NUM_TRUCK_CAPACITY)
    if package_total % config.NUM_TRUCK_CAPACITY:
        minimum_runs += 1
    UI.print(f'{package_total} packages detected, truck capacity is {truck_capacity}', sleep_seconds=2)
    UI.print(f'A minimum of {minimum_runs} runs detected', extra_lines=1, sleep_seconds=2)
    UI.print('Calculating best target locations', think=True, extra_lines=1)
    UI.print('Searching for highest priority package locations', think=True, extra_lines=1)
    earliest_deadline_location = _find_earliest_deadline_packages()
    if earliest_deadline_location:
        best_targets.append(earliest_deadline_location)
    furthest_away_from_hub_location = _find_furthest_location_away(Truck.hub_location)
    best_targets.append(furthest_away_from_hub_location)
    opposite_from_furthest_location = _find_furthest_location_away(furthest_away_from_hub_location)
    best_targets.append(opposite_from_furthest_location)
    if best_targets:
        UI.print(f'{len(best_targets)} viable targets found.', 5, color=Color.GREEN, extra_lines=1)
        best_targets = _analyze_best_targets(best_targets)
        UI.press_enter_to_continue()
        return best_targets
    else:
        UI.print('No viable targets found.', 5, color=Color.RED, extra_lines=1)
        exit(1)


def _analyze_paired_targets(index_number: int, paired_targets: dict):
    truck_id, target_set = copy(paired_targets).popitem()
    UI.print(f'Analyzing {len(target_set)} targets for run #{index_number + 1} - '
             f'"{list(target_set)[0].name}" and "{list(target_set)[1].name}"', color=Color.YELLOW, think=True)
    if truck_id:
        UI.print(f'These locations is assigned to truck #{truck_id}', color=Color.RED, think=True)
        UI.print(f'All locations on this run must also be assigned to truck #{truck_id}', think=True, extra_lines=1)
        if len([location for location in PackageHandler.all_locations if location.assigned_truck_id == truck_id]) >= 4:
            UI.print(f'Multiple locations requiring truck #{truck_id} detected', sleep_seconds=4, color=Color.RED)
            UI.print(f'Prioritizing run focused on deliveries to locations requiring truck #{truck_id}',
                     think=True, extra_lines=2)
    return RunFocus.ASSIGNED_TRUCK


def _analyze_target_location(index_number: int, target_location: Location):
    UI.print(f'Analyzing target run #{index_number + 1} - "{target_location.name}"', color=Color.YELLOW, think=True)
    if target_location.has_early_deadline():
        UI.print(f'This location has packages due be delivered by {target_location.earliest_deadline}',
                 color=Color.RED, think=True)
        UI.print('Prioritizing early route run', sleep_seconds=3)
        UI.print('Locations with delayed packages will be avoided', sleep_seconds=4, extra_lines=1)
    if target_location.has_bundled_package:
        UI.print('This location has packages that must be loaded together with packages from other locations'
                 , color=Color.RED, think=True)
        UI.print('Adding all of these locations to the run if possible, all packages must be loaded, and'
                 ' assigned a truck', sleep_seconds=4, extra_lines=1)
    if target_location.assigned_truck_id:
        truck_number = target_location.assigned_truck_id
        UI.print(f'This location is assigned to truck #{truck_number}', color=Color.RED, think=True)
        UI.print(f'All locations on this run must also be assigned to truck #{truck_number}', think=True, extra_lines=1)
        if target_location.has_bundled_package:
            UI.print(f'Checking if bundled package locations match are required to be assigned to the same truck',
                     think=True)
            if not (PackageHandler.get_bundled_packages(all_location_packages=True)
                    .intersection(PackageHandler.get_assigned_truck_packages())):
                UI.print('No conflicts detected.', sleep_seconds=4, color=Color.GREEN)
            return RunFocus.BUNDLED_PACKAGE


def _initialize_trucks(required_truck_ids: Set[int], number_of_delivery_trucks=config.NUM_DELIVERY_TRUCKS):
    available_trucks: Set[Truck] = {Truck(truck_id) for truck_id in range(1, number_of_delivery_trucks + 1)}
    unavailable_trucks = set()
    for truck_id in required_truck_ids:
        for truck in copy(available_trucks):
            if truck_id == truck.truck_id:
                truck.has_assigned_packages = True
                unavailable_trucks.add(truck)
                available_trucks.remove(truck)
    return available_trucks, unavailable_trucks


def _optimal_hub_return_message():
    UI.print('Detected optimal time to return to hub to reload more packages',
             sleep_seconds=4, color=Color.GREEN)
    UI.print(f'Recommending truck returns to hub between deliveries', think=True, extra_lines=2)


def _unconfirmed_package_delivery_message(run):
    UI.print('Detected a delivery of an unconfirmed package, a time is known for expected confirmation',
             sleep_seconds=4, color=Color.RED)
    UI.print(f'Recommending truck departs at later time to accommodate', think=True)
    UI.print(f'Restarting run creation with new start time', think=True, extra_lines=2)


def _analyze_route_run(index_number: int, run: RouteRun):
    UI.print(f'Run #{index_number + 1} successfully built!', sleep_seconds=3, extra_lines=1)
    UI.print(f'Analysing run #{index_number + 1} with target location: "{run.target_location.name}"',
             think=True, extra_lines=1)
    for location in run.ordered_route:
        if location.is_hub:
            continue
        location_dict = run.run_analysis_dict[location]
        packages = location.package_set
        UI.print(f'{len(packages)} package' + ('s' if len(packages) != 1 else '') +
                 f' | "{location.name}" | Expected arrival time is {location_dict["estimated_time_of_arrival"]}'
                 , sleep_seconds=1, color=Color.BLUE)
        for package in packages:
            UI.print(f'Package ID: {str(package.package_id).zfill(2)} | ' + (f'Has a deadline of {package.deadline}'
                                                                             if package.deadline != config.DELIVERY_RETURN_TIME else 'Has no deadline')
                     + ' | Successful delivery will be achieved!', sleep_seconds=1)
        print()
    UI.print(f'\nThe total expected miles on this run is {run.estimated_mileage} '
             f'with an expected completion time of {run.estimated_completion_time} |'
             f' The package delivery total is {run.package_total()}',
             sleep_seconds=4, color=Color.GREEN, extra_lines=4)


def _select_truck_for_run(target_location: Location, available_truck_pool: Set[Truck],
                          unavailable_truck_pool: Set[Truck]) -> Truck:
    truck = None
    for available_truck in copy(available_truck_pool):
        if isinstance(target_location, Location) and target_location.has_required_truck_package:
            if target_location.assigned_truck_id and available_truck.truck_id == target_location.assigned_truck_id:
                truck = available_truck
        elif isinstance(target_location, dict):
            truck_id, target_set = copy(target_location).popitem()
            if truck_id == available_truck.truck_id:
                truck = available_truck
        else:
            truck = random.choice(list(available_truck_pool))
            break
    # available_truck_pool.remove(truck)
    # unavailable_truck_pool.add(truck)
    if not truck:
        truck_id = None
        if isinstance(target_location, Location) and target_location.assigned_truck_id and unavailable_truck_pool:
            truck_id = target_location.assigned_truck_id
        elif isinstance(target_location, dict):
            paired_target_id, target_set = copy(target_location).popitem()
            truck_id = paired_target_id
        for unavailable_truck in unavailable_truck_pool:
            if unavailable_truck.truck_id == truck_id:
                truck = unavailable_truck
    return truck


def _create_optimized_runs(targets) -> Set[Truck]:
    required_truck_ids = set([pair.keys() for pair in targets if isinstance(pair, dict)].pop())
    UI.print('Finding available delivery trucks', think=True, color=Color.YELLOW)
    available_truck_pool, unavailable_truck_pool = _initialize_trucks(required_truck_ids)
    UI.print(f'{len(available_truck_pool)} trucks found', sleep_seconds=4, extra_lines=1)
    for i, target_location in enumerate(targets):
        run = None
        truck = None
        error_location = None
        focus_type = None
        try:
            if isinstance(target_location, dict):
                focus_type = _analyze_paired_targets(i, target_location)
            else:
                focus_type = _analyze_target_location(i, target_location)
            truck = _select_truck_for_run(target_location, available_truck_pool, unavailable_truck_pool)
            created_run, error, error_location = RunPlanner.build(target_location, truck, focus_type)
            if error:
                run = created_run
                raise error
        except OptimalHubReturnError:
            _optimal_hub_return_message()
        except UnconfirmedPackageDeliveryError:
            _unconfirmed_package_delivery_message(run)
            error_run_start_time = run.run_analysis_dict[error_location]['optimal_hub_departure_time']
            modified_error_start_time = TimeConversion.increment_time(error_run_start_time, time_seconds=-120)
            run, error, error_location = \
                RunPlanner.build(target_location, truck, focus_type, start_time=modified_error_start_time)
        finally:
            _analyze_route_run(i, run)
    UI.press_enter_to_continue()
    return available_truck_pool.union(unavailable_truck_pool)


def _get_unassigned_locations():
    return set([location for location in PackageHandler.all_locations if not location.been_assigned])


class RouteBuilder:
    @staticmethod
    def build_optimized_runs():
        best_targets = _calculate_best_targets()
        assigned_trucks = _create_optimized_runs(best_targets)
