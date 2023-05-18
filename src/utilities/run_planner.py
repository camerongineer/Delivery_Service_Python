from typing import Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion


def _is_valid_fill_in(run: RouteRun, fill_in: Location):
    if ((run.package_total() + fill_in.package_total() > config.NUM_TRUCK_CAPACITY)
            or fill_in.been_assigned or fill_in.is_hub):
        return False
    return True


def _fill_in(run: RouteRun, multiplier=1.75):
    loop_length = len(run.ordered_route) + 1 if run.return_to_hub else len(run.ordered_route)
    best_fill_in_mileage = None
    best_fill_in = None
    best_fill_in_index = None
    for i in range(0, loop_length):
        prior_location = run.ordered_route[i - 1] if i > 0 else Truck.hub_location
        next_location = run.ordered_route[i] if i != len(run.ordered_route) else Truck.hub_location
        for fill_in in PackageHandler.all_locations:
            if not _is_valid_fill_in(run, fill_in):
                continue
            current_distance = prior_location.distance(next_location)
            total_distance = prior_location.distance(fill_in) + fill_in.distance(next_location)
            if total_distance <= (current_distance * multiplier):
                if not best_fill_in or (total_distance - current_distance) < best_fill_in_mileage:
                    best_fill_in_mileage = total_distance - current_distance
                    best_fill_in = fill_in
                    best_fill_in_index = i if next_location != Truck.hub_location else None
    return best_fill_in_index, best_fill_in


def _combine_closest_packages(run: RouteRun, closest_location: Location, next_closest_location: Location, minimum: int):
    combine_packages = PackageHandler.get_closest_packages(run.target_location, minimum=minimum, ignore_assigned=True)
    if combine_packages.intersection(PackageHandler.get_bundled_packages(ignore_assigned=True)):
        combine_packages.update(PackageHandler.get_bundled_packages(ignore_assigned=True))
    closest_packages = PackageHandler.get_closest_packages(closest_location, minimum=minimum, ignore_assigned=True)
    next_closest_packages = PackageHandler.get_closest_packages(next_closest_location, minimum=minimum,
                                                                ignore_assigned=True)
    combine_packages.update(closest_packages.union(next_closest_packages))
    return combine_packages


def _get_optimized_run(run: RouteRun, closest_location: Location, next_closest_location: Location, minimum=8):
    target_packages = _combine_closest_packages(run, closest_location, next_closest_location, minimum=minimum)
    run.locations = PackageHandler.get_package_locations(target_packages)
    next_location = _two_opt(run, run.start_location)
    while next_location:
        current_location = next_location
        run.ordered_route.append(current_location)
        current_location.been_assigned = True
        run.required_packages.update(current_location.package_set)
        next_location = _two_opt(run, current_location)

    fill_in_index, fill_in = _fill_in(run)
    while fill_in:
        if fill_in_index:
            run.ordered_route.insert(fill_in_index, fill_in)
        else:
            run.ordered_route.append(fill_in)
        fill_in.been_assigned = True
        run.required_packages.update(fill_in.package_set)
        fill_in_index, fill_in = _fill_in(run)


def _two_opt(run: RouteRun, in_location: Location) -> Location:
    valid_options = dict()
    for first_location, first_distance in in_location.distance_dict.items():
        if not _is_valid_option(run, first_location):
            continue
        has_second_choice = False
        for second_location, second_distance in first_location.distance_dict.items():
            if _is_valid_option(run, second_location, first_location):
                has_second_choice = True
                miles_to_second = first_distance + first_location.distance(second_location)
                package_total = run.package_total() + first_location.package_total() + second_location.package_total()
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
        return first_location
    return None


def _is_valid_option(run, location: Location, other_location=None) -> bool:
    if location not in run.locations or location.been_assigned or location.is_hub or location is other_location:
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
        if not location.been_routed:
            if location.is_hub or TimeConversion.is_time_at_or_before_other_time(location.latest_package_arrival,
                                                                                 run.target_location.earliest_deadline):
                closest_location = location
                break
    next_closest_location = None
    for location, distance in sorted_location_dict:
        if location is not closest_location and not location.been_routed:
            if location.is_hub or TimeConversion.is_time_at_or_before_other_time(location.latest_package_arrival,
                                                                                 run.target_location.earliest_deadline):
                next_closest_location = location
                break
    return closest_location, next_closest_location


def _set_locations_as_routed(ordered_route):
    for location in ordered_route:
        if not location.is_hub:
            location.been_routed = True


class RunPlanner:

    @staticmethod
    def build(target_location: Location, return_to_hub: bool = True, focused_run: bool = False):
        if target_location.been_assigned or target_location.is_hub:
            return None
        run = RouteRun(return_to_hub=return_to_hub)
        run.start_location = Truck.hub_location
        run.focused_run = focused_run
        run.target_location = target_location
        ordered_route = [run.start_location]
        closest_neighbor, next_closest_neighbor = _get_closest_neighbors(run)
        if closest_neighbor is run.start_location and focused_run:
            ordered_route.append(target_location)
        elif next_closest_neighbor is run.start_location and focused_run:
            ordered_route.append(closest_neighbor)
            ordered_route.append(target_location)
        else:
            _get_optimized_run(run, closest_neighbor, next_closest_neighbor)
        _set_locations_as_routed(ordered_route)
        run.set_estimated_mileage()
        return run
