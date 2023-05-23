from copy import copy
from datetime import time
from typing import Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.constants.run_focus import RunFocus
from src.exceptions.route_builder_error import BundledPackageTruckAssignmentError, InvalidRouteRunError, \
    OptimalHubReturnError, PackageNotArrivedError, UnconfirmedPackageDeliveryError, LateDeliveryError
from src.models.location import Location
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion


def _is_valid_fill_in(run: RouteRun, fill_in: Location):
    if ((not any([location.has_bundled_package for location in run.ordered_route]) and fill_in.has_bundled_package) or
            _in_close_proximity_to_locations(fill_in, _get_delayed_locations(run), distance=.75) or
            _in_close_proximity_to_locations(fill_in, _get_assigned_truck_locations(run), distance=.75) or
            _in_close_proximity_to_locations(fill_in, _get_unconfirmed_locations(run), distance=2.9) or
            fill_in in run.ordered_route):
        return False
    return True


def _fill_in(run: RouteRun, allowable_extra_mileage=3.5):
    best_fill_in_mileage = None
    best_fill_in = None
    best_fill_in_index = None
    for i in range(1, len(run.ordered_route)):
        prior_location = run.ordered_route[i - 1]
        next_location = run.ordered_route[i]
        current_distance = prior_location.distance(next_location)
        for fill_in in _get_available_locations(run.start_time):
            if not _is_valid_option(run, fill_in, set(run.ordered_route)) or not _is_valid_fill_in(run, fill_in):
                continue
            total_distance = prior_location.distance(fill_in) + fill_in.distance(next_location)
            if total_distance <= (current_distance + allowable_extra_mileage):
                if not best_fill_in or (total_distance - current_distance) < best_fill_in_mileage:
                    best_fill_in_mileage = total_distance - current_distance
                    best_fill_in = fill_in
                    best_fill_in_index = i
    if not run.return_to_hub and not best_fill_in and not run.focused_run:
        while run.package_total(set(run.ordered_route)) < config.NUM_TRUCK_CAPACITY:
            last_location_dict = sorted(run.ordered_route[-1].distance_dict.items(), key=lambda _location: _location[1])
            for location, mileage in last_location_dict:
                if mileage <= allowable_extra_mileage:
                    if (_is_valid_fill_in(run, location) and location not in run.ordered_route and
                            run.package_total(set(run.ordered_route).union({location})) < config.NUM_TRUCK_CAPACITY):
                        run.ordered_route.append(location)
                        continue
                elif mileage > allowable_extra_mileage:
                    continue
            break
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
        if (package.location not in _get_available_locations(current_time=run.start_time, ignore_assigned=True) or
                (package.location.assigned_truck_id and package.assigned_truck_id != run.assigned_truck_id)):
            combine_packages.remove(package)
    return combine_packages


def _combine_closest_locations(run: RouteRun, closest_location, next_closest_location, minimum):
    unassigned_locations = [location for location in PackageHandler.all_locations if not location.been_assigned]
    remaining_package_total = sum([len(location.package_set) for location in unassigned_locations])
    if remaining_package_total <= config.NUM_TRUCK_CAPACITY:
        run.locations.update(set(unassigned_locations))
    else:
        run.locations.update({run.target_location, closest_location, next_closest_location})
        available_location_pool = _get_available_locations(run.start_time)
        while len(run.locations) < minimum and len(run.locations) <= len(available_location_pool):
            if any([_location for _location in run.locations if _location.has_bundled_package]):
                bundle_locations = PackageHandler.get_package_locations(
                    PackageHandler.get_bundled_packages(ignore_assigned=True))
                run.locations.update(bundle_locations)
            target_best = _best_closest_location(run, run.target_location)
            closest_best = _best_closest_location(run, closest_location)
            next_best = _best_closest_location(run, next_closest_location)
            best_set = list(filter(lambda _location: _location is not None, [target_best, closest_best, next_best]))
            if not best_set:
                break
            best_one = min(best_set, key=lambda d: min(d.keys()))
            run.locations.add(best_one.popitem()[1])


def _best_closest_location(run, location: Location):
    distance_sorted_dict = sorted(location.distance_dict.items(), key=lambda _location: _location[1])
    best_closest_location = None
    best_mileage = None
    for location, mileage in distance_sorted_dict:
        if (not _is_valid_option(run, location) or location in run.locations or
                _in_close_proximity_to_locations(location, _get_delayed_locations(run), distance=1) or
                _in_close_proximity_to_locations(location, _get_assigned_truck_locations(run), distance=1)):
            continue
        if not best_mileage:
            best_mileage = mileage
            best_closest_location = location
        elif mileage == best_mileage:
            if ((location.has_required_truck_package and run.assigned_truck_id) and
                    (location.assigned_truck_id == run.assigned_truck_id)):
                best_closest_location = location
        else:
            break
    return {best_mileage: best_closest_location} if best_mileage and best_closest_location else None


def _get_focused_targets(run: RouteRun, minimum=8):
    if run.focused_run is RunFocus.ASSIGNED_TRUCK:
        run.locations.add(run.target_location)
        run.locations.update(PackageHandler.get_package_locations(
            PackageHandler.get_assigned_truck_packages(truck_id=run.assigned_truck_id), ignore_assigned=True))

    if len(run.locations) < minimum and run.package_total() <= config.NUM_TRUCK_CAPACITY:
        highest_sum_of_miles_sorted_locations = (sorted(run.locations, key=lambda _location: sum(_location.distance_dict.values())))
        if highest_sum_of_miles_sorted_locations:
            best_target = highest_sum_of_miles_sorted_locations.pop()
            if best_target is run.target_location:
                best_target = highest_sum_of_miles_sorted_locations.pop()
            next_best_target = highest_sum_of_miles_sorted_locations.pop()
            if next_best_target is run.target_location:
                next_best_target = highest_sum_of_miles_sorted_locations.pop()
            _combine_closest_locations(run, best_target, next_best_target, minimum)


def _get_optimized_run(run: RouteRun, minimum=8):
    fill_in_max_mileage = 3

    if run.focused_run:
        _get_focused_targets(run)
        fill_in_max_mileage = 2
    else:
        closest_neighbor, next_closest_neighbor = _get_closest_neighbors(run)
        _combine_closest_locations(run, closest_neighbor, next_closest_neighbor, minimum)

    next_location, following_location = _two_opt(run, run.ordered_route[0])
    while next_location and following_location:
        run.ordered_route.append(next_location)
        run.ordered_route.append(following_location)
        next_location, following_location = _two_opt(run, run.ordered_route[-1])
    while next_location and not following_location:
        run.ordered_route.append(next_location)
        next_location, following_location = _two_opt(run, run.ordered_route[-1])

    if run.return_to_hub:
        run.ordered_route.append(Truck.hub_location)

    fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)
    while fill_in_index:
        run.ordered_route.insert(fill_in_index, fill_in)
        fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)

    run.locations = set(run.ordered_route)
    run.locations.remove(Truck.hub_location)


def _two_opt(run: RouteRun, in_location: Location):
    valid_options, secondary_options = dict(), dict()
    for first_location, first_distance in in_location.distance_dict.items():
        if first_location not in run.locations or first_location in run.ordered_route:
            continue
        for second_location in run.locations:
            if first_location is not second_location and second_location not in run.ordered_route:
                miles_to_second = first_distance + first_location.distance(second_location)
                package_total = _get_estimated_required_package_total(
                    run.ordered_route + [first_location, second_location])
                if run.return_to_hub and package_total >= config.NUM_TRUCK_CAPACITY * .45:
                    miles_to_second += second_location.distance(Truck.hub_location)
                if miles_to_second not in valid_options.keys():
                    valid_options[miles_to_second] = []
                valid_options[miles_to_second].append((first_location, second_location))
                continue
        if first_location is not in_location and not first_location.is_hub:
            if in_location.distance(first_location) not in secondary_options.keys():
                secondary_options[in_location.distance(first_location)] = []
            secondary_options[in_location.distance(first_location)].append((first_location, None))
    return _best_option(run, valid_options, secondary_options)


# def _two_opt(run: RouteRun, in_location: Location):
#     valid_options = dict()
#     distance_sorted_in_location_dict = sorted(in_location.distance_dict.items(), key=lambda _location: _location[1])
#
#     for first_location, first_distance in distance_sorted_in_location_dict:
#         if not _is_valid_option(run, first_location):
#             continue
#         distance_sorted_first_location_dict = sorted(first_location.distance_dict.items(),
#                                                      key=lambda _location: _location[1])
#         has_second_choice = False
#         for second_location, second_distance in distance_sorted_first_location_dict:
#             if _is_valid_option(run, second_location, first_location):
#                 has_second_choice = True
#                 miles_to_second = first_distance + first_location.distance(second_location)
#                 package_total = _get_estimated_required_package_total(
#                     run.ordered_route + [first_location, second_location])
#                 if run.return_to_hub and package_total >= config.NUM_TRUCK_CAPACITY * .45:
#                     miles_to_second += second_location.distance(Truck.hub_location)
#                 if miles_to_second not in valid_options.keys():
#                     valid_options[miles_to_second] = []
#                 valid_options[miles_to_second].append((first_location, second_location))
#         if not has_second_choice:
#             return distance_sorted_in_location_dict[0], None
#     return _best_option(valid_options)


def _best_option(run: RouteRun, valid_options: dict, secondary_options: dict):
    if not valid_options and not secondary_options:
        return None, None
    if not valid_options:
        min_mileage = min([mileage for mileage in secondary_options.keys()])
        first_location, none_location = secondary_options[min_mileage][0]
        return first_location, none_location
    mile_sorted_valid_options = sorted(valid_options.items())
    if len(mile_sorted_valid_options) > 2:
        first_opposite, second_opposite = mile_sorted_valid_options[-1][1][0]
        if first_opposite is run.target_location:
            target = first_opposite
        elif second_opposite is run.target_location:
            target = second_opposite
        else:
            target = (first_opposite if first_opposite.distance(run.target_location) <
                                        second_opposite.distance(run.target_location) else second_opposite)
        for mileage, pair in mile_sorted_valid_options:
            first, second = pair[0]
            if first is target or second is target:
                return first, second
    first_location, second_location = mile_sorted_valid_options[0][1][0]
    return first_location, second_location


def _is_valid_option(run, location: Location, alternate_locations: Set[Location] = None) -> bool:
    available_location_pool = _get_available_locations(run.start_time)
    if alternate_locations:
        estimated_package_total = run.package_total(alternate_locations.union({location}))
    else:
        estimated_package_total = run.package_total(run.locations.union({location}))
    if (location.is_hub or location not in available_location_pool or
            estimated_package_total > config.NUM_TRUCK_CAPACITY or
            ((location.assigned_truck_id is not None and run.assigned_truck_id is not None) and
             (location.assigned_truck_id != run.assigned_truck_id))):
        return False
    return True


def _is_valid_best_option(run, location: Location, other_location=None) -> bool:
    if other_location:
        locations_for_package_total = [location] if not other_location else [location, other_location]
        estimated_package_total = _get_estimated_required_package_total(run.ordered_route + locations_for_package_total)
        if estimated_package_total > config.NUM_TRUCK_CAPACITY:
            return False
    if (location not in run.locations or location is other_location or location in run.ordered_route or
            _in_close_proximity_to_locations(location, _get_delayed_locations(run)) or
            _in_close_proximity_to_locations(location, _get_assigned_truck_locations(run))):
        return False
    return True


def _in_close_proximity_of_undeliverable(run, in_location: Location) -> bool:
    undeliverable_locations = get_undeliverable_locations(run)
    for location in undeliverable_locations:
        if location is in_location or location.distance(in_location) < 1:
            return True
    return False


def get_undeliverable_locations(run: RouteRun):
    undeliverable_locations = set()
    location_package_dict = PackageHandler.get_location_package_dict()
    for location, packages in location_package_dict.items():
        for package in packages:
            if not package.is_verified_address or package.status != DeliveryStatus.AT_HUB or (
                    package.assigned_truck_id and package.assigned_truck_id != run.assigned_truck_id):
                undeliverable_locations.add(location)
    return undeliverable_locations


def _get_delayed_locations(run: RouteRun):
    delayed_packages = PackageHandler.get_delayed_packages(ignore_arrived=True)
    delayed_locations = PackageHandler.get_package_locations(delayed_packages)
    return delayed_locations.difference(_get_available_locations(run.start_time, ignore_assigned=True))


def _get_unconfirmed_locations(run: RouteRun):
    unconfirmed_packages = PackageHandler.get_unconfirmed_packages()
    unconfirmed_locations = PackageHandler.get_package_locations(unconfirmed_packages)
    return unconfirmed_locations.intersection(_get_available_locations(run.start_time, ignore_assigned=True))


def _get_assigned_truck_locations(run: RouteRun):
    all_assigned_truck_packages = PackageHandler.get_assigned_truck_packages()
    all_run_assigned_packages = PackageHandler.get_assigned_truck_packages(truck_id=run.assigned_truck_id)
    all_assigned_truck_locations = PackageHandler.get_package_locations(all_assigned_truck_packages)
    all_run_assigned_locations = PackageHandler.get_package_locations(all_run_assigned_packages)
    return all_assigned_truck_locations - all_run_assigned_locations


def _in_close_proximity_to_locations(in_location: Location, target_locations: Set[Location], distance=1.75) -> bool:
    for location in target_locations:
        if location.been_assigned:
            continue
        if location is in_location or location.distance(in_location) < distance:
            return True
    return False


def _get_closest_neighbors(run: RouteRun):
    sorted_location_dict = sorted(run.target_location.distance_dict.items(), key=lambda _location: _location[1])
    closest_location = None
    for location, distance in sorted_location_dict:
        if (_is_valid_option(run, location, ) and
                not _in_close_proximity_to_locations(location, _get_delayed_locations(run), distance=2.5)):
            closest_location = location
            break
    next_closest_location = None
    for location, distance in sorted_location_dict:
        if (location is not closest_location and _is_valid_option(run, location, ) and
                not _in_close_proximity_to_locations(location, _get_delayed_locations(run), distance=2.5)):
            next_closest_location = location
            break
    return closest_location, next_closest_location


def _set_locations_as_assigned(run: RouteRun):
    for location in run.ordered_route:
        if not location.is_hub:
            if location.has_bundled_package:
                _set_assigned_truck_id_to_bundle_packages(run)
            location.been_assigned = True
            for package in location.package_set:
                if (package.assigned_truck_id is not None and run.assigned_truck_id is not None and
                        package.assigned_truck_id != run.assigned_truck_id):
                    raise InvalidRouteRunError
                package.assigned_truck_id = run.assigned_truck_id


def _set_assigned_truck_id_to_bundle_packages(run):
    try:
        if not run.assigned_truck_id:
            raise BundledPackageTruckAssignmentError
    except BundledPackageTruckAssignmentError:
        truck_id = 1
        run.assigned_truck_id = truck_id
    for location in run.ordered_route:
        if location.has_bundled_package:
            if location.assigned_truck_id and location.assigned_truck_id != run.assigned_truck_id:
                raise InvalidRouteRunError
            for package in location.package_set:
                package.assigned_truck_id = run.assigned_truck_id
                for bundle_package in package.bundled_package_set:
                    bundle_package.location.assigned_truck_id = run.assigned_truck_id
                    bundle_package.assigned_truck_id = run.assigned_truck_id


def _get_available_locations(current_time: time, in_locations=PackageHandler.all_locations, ignore_assigned=True):
    available_locations = set()
    for location in in_locations:
        if ignore_assigned and location.been_assigned or location.is_hub:
            continue
        if _is_earlier_time(location.latest_package_arrival, current_time):
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
    return len(estimated_packages)


def _is_earlier_time(first_time: time, second_time: time):
    return TimeConversion.is_time_at_or_before_other_time(first_time, second_time)


def _get_run_analysis_dict(run: RouteRun):
    run_analysis_dict = dict()
    packages_delivered = list()
    locations_visited = list()
    requirements_met = True
    minimum_optimal_start_time = None
    latest_arrival_time = None
    for i, location in enumerate(run.ordered_route, start=0):
        if location.is_hub:
            continue
        error_type = None
        locations_visited.append(location)
        previous_location = run.ordered_route[i - 1]
        previous_distance = previous_location.distance(location)
        packages_delivered += list(location.package_set)
        estimated_mileage = run.get_estimated_mileage_at_location(location)
        estimated_time = run.get_estimated_time_at_location(location)
        if not latest_arrival_time or not _is_earlier_time(location.latest_package_arrival, latest_arrival_time):
            latest_arrival_time = location.latest_package_arrival
        departure_requirement_met = _is_earlier_time(location.latest_package_arrival, run.start_time)
        delivery_time_requirement_met = _is_earlier_time(estimated_time, location.earliest_deadline)
        if not delivery_time_requirement_met:
            error_type = PackageNotArrivedError
        if location.has_unconfirmed_package:
            for package in location.package_set:
                if package.package_id in config.EXCEPTED_UPDATES.keys():
                    expected_update_time = config.EXCEPTED_UPDATES[package.package_id]['update_time']
                    if not _is_earlier_time(expected_update_time, estimated_time):
                        delivery_time_requirement_met = False
                        error_type = UnconfirmedPackageDeliveryError
        if not departure_requirement_met:
            error_type = LateDeliveryError
        if not delivery_time_requirement_met or not departure_requirement_met:
            requirements_met = False
        estimated_mileage_to_hub = estimated_mileage + location.hub_distance
        estimated_time_at_hub_arrival = TimeConversion.convert_miles_to_time(estimated_mileage_to_hub, run.start_time)
        hub_insert_distance = previous_location.hub_distance + location.hub_distance
        difference = hub_insert_distance - previous_distance
        seconds_from_hub = TimeConversion.get_seconds_between_times(run.start_time, estimated_time)
        optimal_hub_departure_time = TimeConversion.increment_time(location.earliest_deadline, -seconds_from_hub)
        if not minimum_optimal_start_time or (_is_earlier_time(optimal_hub_departure_time, minimum_optimal_start_time)
                                              and not _is_earlier_time(optimal_hub_departure_time, latest_arrival_time)
                                              ):
            minimum_optimal_start_time = optimal_hub_departure_time
        undelivered_package_total = run.package_total() - len(packages_delivered)
        run_analysis_dict[location] = {
            'previous_location': previous_location,
            'miles_from_previous': previous_distance,
            'estimated_mileage_of_arrival': estimated_mileage,
            'estimated_time_of_arrival': estimated_time,
            'latest_allowable_delivery_time': copy(location.earliest_deadline),
            'latest_allowable_hub_departure': copy(location.latest_package_arrival),
            'undelivered_package_total': undelivered_package_total,
            'departure_requirement_met': departure_requirement_met,
            'delivery_time_requirement_met': delivery_time_requirement_met,
            'packages_delivered': copy(packages_delivered),
            'locations_visited': copy(locations_visited),
            'estimated_mileage_to_hub': estimated_mileage_to_hub,
            'estimated_time_of_hub_arrival': copy(estimated_time_at_hub_arrival),
            'miles_from_previous_with_hub_insert': hub_insert_distance,
            'difference': difference,
            'is_valid_run_at_location': requirements_met,
            'optimal_hub_departure_time': copy(optimal_hub_departure_time),
            'minimum_optimal_time_at_location': copy(minimum_optimal_start_time),
            'error_type': error_type
        }
    return run_analysis_dict


def _simulate_load(run: RouteRun, truck: Truck):
    for location in run.ordered_route:
        if location.is_hub:
            continue
        for package in location.package_set:
            truck.add_package(package)
            if package.bundled_package_set:
                for bundle_package in package.bundled_package_set:
                    truck.add_package(bundle_package)
    run.required_packages = truck.unload()


def _check_requirements_met(run: RouteRun):
    for location in run.ordered_route:
        if location.is_hub:
            continue
        if not run.run_analysis_dict[location]['is_valid_run_at_location']:
            if run.run_analysis_dict[location]['error_type']:
                return run, run.run_analysis_dict[location]['error_type'], location
    return run, None, None


def _check_optimal_return_to_hub(run: RouteRun):
    if (run.package_total() + sum([len(location.package_set) for location in PackageHandler.all_locations
                                   if location.been_assigned]) != len(PackageHandler.all_packages)):
        for i, location in enumerate(run.ordered_route):
            if location.is_hub or location not in run.run_analysis_dict:
                continue
            previous_location = run.ordered_route[i - 1]
            mileage_difference = run.run_analysis_dict[location]['difference']
            packages_delivered = (run.run_analysis_dict[previous_location]['packages_delivered']
                                  if not previous_location.is_hub else set())
            try:
                if 0 < mileage_difference <= config.HUB_RETURN_INSERTION_ALLOWANCE and len(packages_delivered) >= 8:
                    raise OptimalHubReturnError
            except OptimalHubReturnError:
                run.ordered_route = run.ordered_route[:i] + [Truck.hub_location]
                run.run_analysis_dict = _get_run_analysis_dict(run)
                run.locations = set(run.ordered_route)
                run.locations.remove(Truck.hub_location)
                return run, OptimalHubReturnError, None
    return run, None, None


def _analyze_run(run: RouteRun, truck: Truck):
    run_analysis_dict = _get_run_analysis_dict(run)
    run.run_analysis_dict = run_analysis_dict
    run, error, error_location = _check_requirements_met(run)
    if error:
        return run, error, error_location
    run, error, error_location = _check_optimal_return_to_hub(run)
    _simulate_load(run, truck)
    return run, error, error_location


class RunPlanner:

    @staticmethod
    def build(target_location, truck: Truck, run_focus: RunFocus = None, start_time=config.DELIVERY_DISPATCH_TIME):
        run = RouteRun(start_time=start_time)
        run.target_location = target_location
        run.assigned_truck_id = truck.truck_id
        if isinstance(target_location, dict):
            paired_target_id, target_set = copy(target_location).popitem()
            run.target_location = sorted(target_set, key=lambda _target: _target.hub_distance, reverse=True).pop()
            run.assigned_truck_id = paired_target_id
        elif target_location.been_assigned or target_location.is_hub:
            return
        run.focused_run = run_focus
        latest_delayed_time = max([package.hub_arrival_time for package in PackageHandler.get_delayed_packages()])
        if (not _is_earlier_time(run.target_location.earliest_deadline, latest_delayed_time) and
                run.start_time == config.DELIVERY_DISPATCH_TIME):
            run.start_time = latest_delayed_time
        run.ordered_route = [Truck.hub_location]
        _get_optimized_run(run)
        run, error, error_location = _analyze_run(run, truck)
        if error and error is not OptimalHubReturnError:
            return run, error, error_location
        _set_locations_as_assigned(run)
        run.set_required_packages()
        run.set_estimated_mileage()
        run.set_estimated_completion_time()
        run.set_assigned_truck_id()
        truck.route_runs.append(run)
        return run, error, error_location
