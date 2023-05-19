from copy import copy
from datetime import time
from typing import Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.exceptions.route_builder_error import BundledPackageTruckAssignmentError, InvalidRouteRunError
from src.models.location import Location
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion


def _is_valid_fill_in(run: RouteRun, fill_in: Location):
    has_different_assigned_truck_id = any(
        _location for _location in run.ordered_route if _location.assigned_truck != fill_in.assigned_truck)
    if (fill_in.is_hub or (_get_estimated_required_package_total(run.ordered_route + [fill_in]) > config.NUM_TRUCK_CAPACITY)
            or fill_in in run.ordered_route or (run.ignore_delayed_locations and fill_in.has_delayed_packages()) or
            (not any([location.has_bundled_package for location in run.ordered_route]) and fill_in.has_bundled_package) or
            (fill_in.assigned_truck and has_different_assigned_truck_id)
    ):
        return False
    return True


def _fill_in(run: RouteRun, allowable_extra_mileage=3):
    best_fill_in_mileage = None
    best_fill_in = None
    best_fill_in_index = None
    for i in range(1, len(run.ordered_route)):
        prior_location = run.ordered_route[i - 1]
        next_location = run.ordered_route[i]
        for fill_in in PackageHandler.all_locations:
            if not _is_valid_fill_in(run, fill_in):
                continue
            current_distance = prior_location.distance(next_location)
            total_distance = prior_location.distance(fill_in) + fill_in.distance(next_location)
            if total_distance <= (current_distance + allowable_extra_mileage):
                if not best_fill_in or (total_distance - current_distance) < best_fill_in_mileage:
                    best_fill_in_mileage = total_distance - current_distance
                    best_fill_in = fill_in
                    best_fill_in_index = i
    return best_fill_in_index, best_fill_in


def _combine_closest_packages(run: RouteRun, closest_location: Location, next_closest_location: Location, minimum: int):
    combine_packages = PackageHandler.get_closest_packages(run.target_location, minimum=minimum, ignore_assigned=True)
    if len(combine_packages.intersection(PackageHandler.get_bundled_packages(ignore_assigned=True))) > 3:
        combine_packages.update(PackageHandler.get_bundled_packages(ignore_assigned=True))
    closest_packages = PackageHandler.get_closest_packages(closest_location, minimum=minimum, ignore_assigned=True)
    next_closest_packages = PackageHandler.get_closest_packages(next_closest_location, minimum=minimum,
                                                                ignore_assigned=True)
    combine_packages.update(closest_packages.union(next_closest_packages))
    combine_packages_copy = copy(combine_packages)
    for package in combine_packages_copy:
        if package.location not in _get_available_locations(current_time=run.start_time, ignore_assigned=True):
            combine_packages.remove(package)
    return combine_packages


def _get_optimized_run(run: RouteRun, closest_location: Location, next_closest_location: Location, minimum=8):
    fill_in_max_mileage = 1.5 if run.focused_run else 3
    target_packages = _combine_closest_packages(run, closest_location, next_closest_location, minimum=minimum)
    run.locations = PackageHandler.get_package_locations(target_packages)
    run.locations &= _get_available_locations(run.start_time)
    next_location, following_location = _two_opt(run, run.ordered_route[0])
    if not run.focused_run:
        while next_location and following_location:
            current_location = next_location
            run.ordered_route.append(current_location)
            run.ordered_route.append(current_location)
            print(run.get_estimated_time_at_location(Truck.hub_location))
            next_location, following_location = _two_opt(run, current_location)

    else:
        run.ordered_route.append(run.target_location)
    if run.return_to_hub:
        run.ordered_route.append(Truck.hub_location)

    fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)
    while fill_in:
        run.ordered_route.insert(fill_in_index, fill_in)
        print(run.get_estimated_time_at_location(Truck.hub_location))
        fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)

    run.locations = run.locations.intersection(set(run.ordered_route))
    run.locations.update(set(run.ordered_route))
    run.locations.remove(Truck.hub_location)


def _two_opt(run: RouteRun, in_location: Location):
    valid_options = dict()
    for first_location, first_distance in in_location.distance_dict.items():
        if not _is_valid_option(run, first_location):
            continue
        has_second_choice = False
        for second_location, second_distance in first_location.distance_dict.items():
            if _is_valid_option(run, second_location, first_location):
                has_second_choice = True
                miles_to_second = first_distance + first_location.distance(second_location)
                package_total = _get_estimated_required_package_total(run.ordered_route + [first_location, second_location])
                if run.return_to_hub and package_total >= config.NUM_TRUCK_CAPACITY * .45:
                    miles_to_second += second_location.distance(Truck.hub_location)
                if miles_to_second not in valid_options.keys():
                    valid_options[miles_to_second] = []
                valid_options[miles_to_second].append((first_location, second_location))
        if not has_second_choice:
            return first_location
    return _best_option(run, valid_options)


def _best_option(run, valid_options: dict):
    if not valid_options:
        return None
    min_mileage = min([mileage for mileage in valid_options.keys()])
    if min_mileage:
        first_location, second_location = valid_options[min_mileage][0]
        return first_location, second_location
    return None


def _is_valid_option(run, location: Location, other_location=None) -> bool:
    has_different_assigned_truck_id = any(
        _location for _location in run.ordered_route if _location.assigned_truck != location.assigned_truck)
    if (location not in run.locations or (location in run.ordered_route) or location is other_location or
            location.is_hub or (location.assigned_truck and has_different_assigned_truck_id)):
        return False
    return True


def _in_close_proximity_of_undeliverable(run, in_location: Location) -> bool:
    undeliverable_locations = get_undeliverable_locations(run)
    for location in undeliverable_locations:
        if location is in_location or location.distance(in_location) < 1:
            return True
    return False


def get_undeliverable_locations(run):
    undeliverable_locations = set()
    location_package_dict = PackageHandler.get_location_package_dict()
    for location, packages in location_package_dict.items():
        for package in packages:
            if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (
                    package.assigned_truck_id and package.assigned_truck_id != run.assigned_truck_id):
                undeliverable_locations.add(location)
    return undeliverable_locations


def _get_closest_neighbors(run: RouteRun):
    sorted_location_dict = sorted(run.target_location.distance_dict.items(), key=lambda _location: _location[1])
    closest_location = None
    for location, distance in sorted_location_dict:
        if not location.been_assigned and not location.is_hub and location in _get_available_locations(run.start_time):
            if location.is_hub or TimeConversion.is_time_at_or_before_other_time(location.latest_package_arrival,
                                                                                 run.target_location.earliest_deadline):
                closest_location = location
                break
    next_closest_location = None
    for location, distance in sorted_location_dict:
        if location is not closest_location and not location.been_assigned and not location.is_hub and location in _get_available_locations(run.start_time):
            if location.is_hub or TimeConversion.is_time_at_or_before_other_time(location.latest_package_arrival,
                                                                                 run.target_location.earliest_deadline):
                next_closest_location = location
                break
    return closest_location, next_closest_location


def _set_locations_as_assigned(run: RouteRun):
    for location in run.ordered_route:
        if not location.is_hub:
            if location.has_bundled_package:
                _set_assigned_truck_id_to_bundle_packages(run)
            location.been_assigned = True


def _set_assigned_truck_id_to_bundle_packages(run):
    try:
        if not run.assigned_truck_id:
            raise BundledPackageTruckAssignmentError
    except BundledPackageTruckAssignmentError:
        print('Please give the run a truck ID')
        truck_id = int(input())
        run.assigned_truck_id = truck_id
    for location in run.ordered_route:
        if location.has_bundled_package:
            if location.assigned_truck and location.assigned_truck != run.assigned_truck_id:
                raise InvalidRouteRunError
            for package in location.package_set:
                package.assigned_truck_id = run.assigned_truck_id
                for bundle_package in package.bundled_package_set:
                    bundle_package.location.assigned_truck = run.assigned_truck_id
                    bundle_package.assigned_truck_id = run.assigned_truck_id


def _get_available_locations(current_time: time, in_locations=PackageHandler.all_locations, ignore_assigned=True):
    available_locations = set()
    for location in in_locations:
        if ignore_assigned and location.been_assigned or location.is_hub:
            continue
        if TimeConversion.is_time_at_or_before_other_time(location.latest_package_arrival, current_time):
            available_locations.add(location)
    return available_locations


def _get_estimated_required_package_total(ordered_route_with_new_locations):
    estimated_packages = set()
    for location in ordered_route_with_new_locations:
        if location.is_hub:
            continue
        estimated_packages.update(location.package_set)
    for package in copy(estimated_packages):
        if package.bundled_package_set:
            estimated_packages.update(package.bundled_package_set)
    for package in copy(estimated_packages):
        if package.location.been_assigned:
            estimated_packages.remove(package)
    return len(estimated_packages)


class RunPlanner:

    @staticmethod
    def build(target_location: Location, return_to_hub=True, focused_run=False,
              ignore_delayed_locations=False, start_time=config.DELIVERY_DISPATCH_TIME):
        if target_location.been_assigned or target_location.is_hub:
            return None
        run = RouteRun(return_to_hub=return_to_hub, start_time=start_time)
        run.focused_run = focused_run
        run.ignore_delayed_locations = ignore_delayed_locations
        run.target_location = target_location
        run.ordered_route = [Truck.hub_location]
        closest_neighbor, next_closest_neighbor = _get_closest_neighbors(run)
        _get_optimized_run(run, closest_neighbor, next_closest_neighbor)
        _set_locations_as_assigned(run)
        run.set_required_packages()
        run.set_estimated_mileage()
        run.set_estimated_completion_time()
        run.set_assigned_truck_id()
        return run
