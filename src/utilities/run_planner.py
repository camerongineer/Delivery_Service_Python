from copy import copy
from datetime import time
from typing import Set

from src import config
from src.constants.run_focus import RunFocus
from src.constants.run_info import RunInfo
from src.exceptions.route_builder_error import (BundledPackageTruckAssignmentError, InvalidRouteRunError,
                                                OptimalHubReturnError, PackageNotArrivedError,
                                                UnconfirmedPackageDeliveryError, LateDeliveryError)
from src.models.location import Location
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.time_conversion import TimeConversion


__all__ = ['RunPlanner']


def _best_closest_location(run, location: Location):
    """
    Find the best closest location based on the given location and run.

    Args:
        run (RouteRun): The route run.
        location (Location): The current location.

    Returns:
        dict: A dictionary containing the best mileage and closest location.

    Time Complexity: O(n log n)

    Space Complexity: O(1).

    """
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


def _combine_closest_locations(run: RouteRun, closest_location, next_closest_location, minimum):
    """
    Combine the closest locations with the run based on certain conditions.

    Args:
        run (RouteRun): The route run.
        closest_location (Location): The closest location.
        next_closest_location (Location): The next closest location.
        minimum (int): The minimum number of locations to be combined.

    Time Complexity: O(n)

    Space Complexity: O(1)
    """
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


def _get_focused_targets(run: RouteRun, minimum=8):
    """
    Get the focused targets for the route run based on the run's focus and other conditions.

    Args:
        run (RouteRun): The route run.
        minimum (int, optional): The minimum number of locations. Defaults to 8.

    Time Complexity: O(n log n)

    Space Complexity: O(1)
    """
    if run.focused_run is RunFocus.ASSIGNED_TRUCK:
        run.locations.add(run.target_location)
        run.locations.update(PackageHandler.get_package_locations(
            PackageHandler.get_assigned_truck_packages(truck_id=run.assigned_truck_id), ignore_assigned=True))

    if len(run.locations) < minimum and run.package_total() <= config.NUM_TRUCK_CAPACITY:
        highest_sum_of_miles_sorted_locations = (sorted(run.locations,
                                                        key=lambda _location: sum(_location.distance_dict.values())))
        if highest_sum_of_miles_sorted_locations:
            best_target = highest_sum_of_miles_sorted_locations.pop()
            if best_target is run.target_location:
                best_target = highest_sum_of_miles_sorted_locations.pop()
            next_best_target = highest_sum_of_miles_sorted_locations.pop()
            if next_best_target is run.target_location:
                next_best_target = highest_sum_of_miles_sorted_locations.pop()
            _combine_closest_locations(run, best_target, next_best_target, minimum)


def _is_valid_option(run: RouteRun, location: Location, alternate_locations: Set[Location] = None) -> bool:
    """
    Check if a location is a valid option for inclusion in the run based on certain conditions.

    Args:
        run (RouteRun): The route run.
        location (Location): The location to check.
        alternate_locations (Set[Location], optional): Alternate locations to consider along with the run's current locations. Defaults to None.

    Returns:
        bool: True if the location is a valid option, False otherwise.

    Time Complexity: O(n)

    Space Complexity: O(1)
    """
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


def _is_valid_fill_in(run: RouteRun, fill_in: Location):
    """
    Check if a location is a valid fill-in option for the run based on certain conditions.

    Args:
        run (RouteRun): The route run.
        fill_in (Location): The location to check.

    Returns:
        bool: True if the location is a valid fill-in option, False otherwise.

    Time Complexity: O(n)

    Space Complexity: O(1)
    """
    if ((not any([location.has_bundled_package for location in run.ordered_route]) and fill_in.has_bundled_package) or
            _in_close_proximity_to_locations(fill_in, _get_delayed_locations(run), distance=.75) or
            _in_close_proximity_to_locations(fill_in, _get_assigned_truck_locations(run), distance=.75) or
            _in_close_proximity_to_locations(fill_in, _get_unconfirmed_locations(run), distance=3) or
            fill_in in run.ordered_route):
        return False
    return True


def _fill_in(run: RouteRun, allowable_extra_mileage=3.5):
    """
    Fill in the route run with additional locations based on certain conditions.

    Args:
        run (RouteRun): The route run.
        allowable_extra_mileage (float, optional): The allowable extra mileage for fill-in locations. Defaults to 3.5.

    Returns:
        Tuple[int, Location]: The index and location of the best fill-in option.

    Time Complexity: O(n^3)

    Space Complexity: O(1)
    """
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


def _two_closest(run: RouteRun, in_location: Location):
    """
    Find the two closest locations to the given location.

    Args:
        run (RouteRun): The route run.
        in_location (Location): The input location.

    Returns:
        Tuple[Location, Location]: The two closest locations.

    Time Complexity: O(n^2)
    Space Complexity: O(n)
    """

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


def _best_option(run: RouteRun, valid_options: dict, secondary_options: dict):
    """
    Find the best option from the valid options and secondary options.

    Args:
        run (RouteRun): The route run.
        valid_options (dict): Valid options dictionary.
        secondary_options (dict): Secondary options dictionary.

    Returns:
        Tuple[Location, Location]: The best option pair.

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """

    if not valid_options and not secondary_options:
        return None, None
    if not valid_options:
        min_mileage = min([mileage for mileage in secondary_options.keys()])
        first_location, none_location = secondary_options[min_mileage][0]
        return first_location, none_location
    mile_sorted_valid_options = sorted(valid_options.items())
    if len(mile_sorted_valid_options) > 2:
        minimum_mileage = None
        best_pair = None
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
            if not minimum_mileage:
                minimum_mileage = mileage
                best_pair = first, second
            if minimum_mileage + 1.5 < mileage:
                return best_pair
            elif first is target or second is target:
                return first, second
    first_location, second_location = mile_sorted_valid_options[0][1][0]
    return first_location, second_location


def _get_closest_neighbors(run: RouteRun):
    """
    Get the closest and next closest neighbors of the target location.

    Args:
        run (RouteRun): The route run.

    Returns:
        Tuple[Location, Location]: The closest and next closest locations.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

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


def _get_optimized_run(run: RouteRun, minimum=config.CLOSEST_NEIGHBOR_MINIMUM):
    """
    Get the optimized route run by combining the closest locations and filling in gaps.

    Args:
        run (RouteRun): The route run.
        minimum (int): The minimum number of locations to be combined.

    Time Complexity: O(n^2)
    Space Complexity: O(n)
    """

    fill_in_max_mileage = config.FILL_IN_INSERTION_ALLOWANCE
    if run.focused_run:
        _get_focused_targets(run)
        fill_in_max_mileage = fill_in_max_mileage * .5
    else:
        closest_neighbor, next_closest_neighbor = _get_closest_neighbors(run)
        _combine_closest_locations(run, closest_neighbor, next_closest_neighbor, minimum)

    next_location, following_location = _two_closest(run, run.ordered_route[0])
    while next_location and following_location:
        run.ordered_route.append(next_location)
        run.ordered_route.append(following_location)
        next_location, following_location = _two_closest(run, run.ordered_route[-1])
    while next_location and not following_location:
        run.ordered_route.append(next_location)
        next_location, following_location = _two_closest(run, run.ordered_route[-1])

    if run.return_to_hub:
        run.ordered_route.append(Truck.hub_location)

    fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)
    while fill_in_index:
        run.ordered_route.insert(fill_in_index, fill_in)
        fill_in_index, fill_in = _fill_in(run, allowable_extra_mileage=fill_in_max_mileage)

    run.locations = set(run.ordered_route)
    run.locations.remove(Truck.hub_location)


def _is_valid_insert(previous_location: Location, location: Location, insert_location: Location, run_analysis_dict):
    """
    Check if inserting a location between previous_location and location is valid.

    Args:
        previous_location (Location): The previous location.
        location (Location): The current location.
        insert_location (Location): The location to be inserted.
        run_analysis_dict (dict): The run analysis dictionary.

    Returns:
        bool: True if the insert is valid, False otherwise.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    next_location = run_analysis_dict[(previous_location, location)][RunInfo.NEXT_LOCATION]
    miles_from_previous = run_analysis_dict[(previous_location, location)][RunInfo.MILES_FROM_PREVIOUS]
    miles_to_next = run_analysis_dict[(previous_location, location)][RunInfo.MILES_TO_NEXT] if next_location else 0
    current_mileage = miles_from_previous + miles_to_next
    if (insert_location.distance(location) * 2) > current_mileage:
        return False
    miles_from_previous_to_next = (previous_location.distance(next_location)
                                   if next_location and previous_location else 0)
    new_mileage = (insert_location.distance(location) * 2) + miles_from_previous_to_next

    return current_mileage - new_mileage > 0


def _optimized_revisit(run: RouteRun):
    """
    Revisit the ordered route and optimize the order of locations.

    Args:
        run (RouteRun): The route run.

    Time Complexity: O(n^2)
    Space Complexity: O(n)
    """

    while True:
        was_changed = False
        ordered_route_copy = run.ordered_route[:]
        for i, location in enumerate(run.ordered_route):
            if i == 0:
                continue
            previous_location = run.ordered_route[i - 1]
            if run.run_analysis_dict[(previous_location, location)][RunInfo.MILES_FROM_PREVIOUS] > 2:
                best_mileage = None
                best_insert = None
                for j in range(len(run.ordered_route)):
                    insert_location = run.ordered_route[j]
                    if insert_location is location or insert_location.is_hub:
                        continue
                    if _is_valid_insert(previous_location, location, insert_location, run.run_analysis_dict):
                        if not best_mileage or insert_location.distance(location) < best_mileage:
                            best_mileage = insert_location.distance(location)
                            best_insert = insert_location
                if best_insert:
                    location = ordered_route_copy.pop(ordered_route_copy.index(location))
                    best_insert_index = ordered_route_copy.index(best_insert)
                    ordered_route_copy.insert(best_insert_index, best_insert)
                    first_half = ordered_route_copy[:best_insert_index + 1]
                    second_half = ordered_route_copy[best_insert_index + 1:]
                    first_half += [location]
                    ordered_route_copy = first_half + second_half
                    run.ordered_route = ordered_route_copy
                    run.run_analysis_dict = _get_run_analysis_dict(run)
                    was_changed = True
                    break
        if not was_changed:
            break


def _get_delayed_locations(run: RouteRun):
    """
    Get the locations of delayed packages that are not available for the given route run.

    Args:
        run (RouteRun): The route run.

    Returns:
        set: The set of delayed locations.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    delayed_packages = PackageHandler.get_delayed_packages(ignore_arrived=True)
    delayed_locations = PackageHandler.get_package_locations(delayed_packages)
    return delayed_locations.difference(_get_available_locations(run.start_time, ignore_assigned=True))


def _get_unconfirmed_locations(run: RouteRun):
    """
    Get the locations of unconfirmed packages that are available for the given route run.

    Args:
        run (RouteRun): The route run.

    Returns:
        set: The set of unconfirmed locations.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    unconfirmed_packages = PackageHandler.get_unconfirmed_packages()
    unconfirmed_locations = PackageHandler.get_package_locations(unconfirmed_packages)
    return unconfirmed_locations.intersection(_get_available_locations(run.start_time, ignore_assigned=True))


def _get_assigned_truck_locations(run: RouteRun):
    """
    Get the locations of packages assigned to other trucks but not assigned to the given route run.

    Args:
        run (RouteRun): The route run.

    Returns:
        set: The set of assigned truck locations.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    all_assigned_truck_packages = PackageHandler.get_assigned_truck_packages()
    all_run_assigned_packages = PackageHandler.get_assigned_truck_packages(truck_id=run.assigned_truck_id)
    all_assigned_truck_locations = PackageHandler.get_package_locations(all_assigned_truck_packages)
    all_run_assigned_locations = PackageHandler.get_package_locations(all_run_assigned_packages)
    return all_assigned_truck_locations - all_run_assigned_locations


def _in_close_proximity_to_locations(in_location: Location, target_locations: Set[Location], distance=1.75) -> bool:
    """
    Check if the given location is in close proximity to any of the target locations.

    Args:
        in_location (Location): The input location.
        target_locations (set): The set of target locations.
        distance (float): The distance threshold for proximity.

    Returns:
        bool: True if the location is in close proximity to any of the target locations, False otherwise.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    for location in target_locations:
        if location.been_assigned:
            continue
        if location is in_location or location.distance(in_location) < distance:
            return True
    return False


def _set_locations_as_assigned(run: RouteRun):
    """
    Set the locations in the ordered route as assigned for the given route run.

    Args:
        run (RouteRun): The route run.

    Time Complexity: O(n * m)
    Space Complexity: O(1)
    """

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
    """
    Assigns the truck ID to the bundled packages in the route run's ordered route.

    Args:
        run (RouteRun): The route run.

    Raises:
        BundledPackageTruckAssignmentError: If the route run does not have an assigned truck ID.
        InvalidRouteRunError: If a bundled package's location already has a different assigned truck ID.

    Time Complexity: O(n * m), where n is the number of locations in the ordered route.
    Space Complexity: O(1)
    """

    if not run.assigned_truck_id:
        raise BundledPackageTruckAssignmentError
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
    """
    Returns the set of available locations based on the current time.

    Args:
        current_time (time): The current time.
        in_locations (Set[Location]): The set of locations to consider.
        ignore_assigned (bool): Whether to ignore locations that have already been assigned.

    Returns:
        Set[Location]: The available locations.

    Time Complexity: O(n), where n is the number of locations in the input set.
    Space Complexity: O(1)
    """

    available_locations = set()
    for location in in_locations:
        if ignore_assigned and location.been_assigned or location.is_hub:
            continue
        if _is_earlier_time(location.latest_package_arrival, current_time):
            available_locations.add(location)
    return available_locations


def _get_estimated_required_package_total(ordered_route_with_new_locations):
    """
    Calculates the estimated total number of packages required for the ordered route with new locations.

    Args:
        ordered_route_with_new_locations (List[Location]): The ordered route with new locations.

    Returns:
        int: The estimated total number of packages required to be on the truck.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

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
    """
    Checks if the first time is earlier than or equal to the second time.

    Args:
        first_time (time): The first time.
        second_time (time): The second time.

    Returns:
        bool: True if the first time is earlier than or equal to the second time, False otherwise.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    return TimeConversion.is_time_at_or_before_other_time(first_time, second_time)


def _get_run_analysis_dict(run: RouteRun):
    """
    Generates a dictionary containing analysis information for each location in the route run.

    Args:
        run (RouteRun): The route run.

    Returns:
        dict: A dictionary containing analysis information for each location.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    run_analysis_dict = dict()
    packages_delivered = set()
    locations_visited = list()
    requirements_met = True
    minimum_optimal_start_time = None
    latest_arrival_time = None
    for i, location in enumerate(run.ordered_route, start=0):
        previous_location = run.ordered_route[i - 1] if i > 0 else None
        error_type = None
        error_location = None
        previous_distance = previous_location.distance(location) if previous_location else 0
        locations_visited.append(location)
        next_location = run.ordered_route[i + 1] if i + 1 < len(run.ordered_route) else None
        next_distance = location.distance(next_location) if next_location else None
        if not location.is_hub:
            packages_delivered.update(location.package_set)
        estimated_mileage = run.get_estimated_mileage_at_location(index=i)
        estimated_time = TimeConversion.convert_miles_to_time(estimated_mileage, origin_time=run.start_time)
        estimated_mileage_at_next = run.get_estimated_mileage_at_location(index=i + 1) if next_location else None
        estimated_time_at_next = TimeConversion.convert_miles_to_time(
            estimated_mileage_at_next, origin_time=run.start_time) if next_location else None
        departure_requirement_met = True
        delivery_time_requirement_met = True
        if not location.is_hub:
            if not latest_arrival_time or not _is_earlier_time(location.latest_package_arrival, latest_arrival_time):
                latest_arrival_time = location.latest_package_arrival
            departure_requirement_met = _is_earlier_time(location.latest_package_arrival, run.start_time)
            delivery_time_requirement_met = _is_earlier_time(estimated_time, location.earliest_deadline)
        if not delivery_time_requirement_met:
            error_type = LateDeliveryError
        if location.has_unconfirmed_package:
            for package in location.package_set:
                if package.package_id in config.EXCEPTED_UPDATES.keys():
                    expected_update_time = config.EXCEPTED_UPDATES[package.package_id]['update_time']
                    if not _is_earlier_time(expected_update_time, estimated_time):
                        delivery_time_requirement_met = False
                        error_type = UnconfirmedPackageDeliveryError
        if not departure_requirement_met:
            error_type = PackageNotArrivedError
        if not delivery_time_requirement_met or not departure_requirement_met:
            requirements_met = False
            if not error_location:
                error_location = (previous_location, location)
        estimated_mileage_to_hub = estimated_mileage + location.hub_distance
        estimated_time_at_hub_arrival = TimeConversion.convert_miles_to_time(estimated_mileage_to_hub, run.start_time)
        hub_insert_distance = 0 if location.is_hub else previous_location.hub_distance + location.hub_distance
        difference = 0 if location.is_hub else hub_insert_distance - previous_distance
        seconds_from_hub = TimeConversion.get_seconds_between_times(run.start_time, estimated_time)
        optimal_hub_departure_time = TimeConversion.increment_time(location.earliest_deadline, -seconds_from_hub)
        if not minimum_optimal_start_time or (_is_earlier_time(optimal_hub_departure_time, minimum_optimal_start_time)
                                              and not _is_earlier_time(optimal_hub_departure_time, latest_arrival_time)
        ):
            minimum_optimal_start_time = optimal_hub_departure_time
        undelivered_package_total = run.package_total() - len(packages_delivered)
        run_analysis_dict[(previous_location, location)] = {
            RunInfo.PREVIOUS_LOCATION: previous_location,
            RunInfo.MILES_FROM_PREVIOUS: previous_distance,
            RunInfo.NEXT_LOCATION: next_location,
            RunInfo.MILES_TO_NEXT: next_distance,
            RunInfo.ESTIMATED_MILEAGE: estimated_mileage,
            RunInfo.ESTIMATED_TIME: estimated_time,
            RunInfo.ESTIMATED_MILEAGE_AT_NEXT: estimated_mileage_at_next,
            RunInfo.ESTIMATED_TIME_AT_NEXT: estimated_time_at_next,
            RunInfo.LATEST_ALLOWED_DELIVERY_TIME: copy(location.earliest_deadline),
            RunInfo.LATEST_ALLOWED_HUB_DEPARTURE: copy(location.latest_package_arrival),
            RunInfo.UNDELIVERED_PACKAGES_TOTAL: undelivered_package_total,
            RunInfo.DEPARTURE_REQUIREMENT_MET: departure_requirement_met,
            RunInfo.DELIVERY_TIME_REQUIREMENT_MET: delivery_time_requirement_met,
            RunInfo.PACKAGES_DELIVERED: copy(packages_delivered),
            RunInfo.LOCATIONS_VISITED: copy(locations_visited),
            RunInfo.ESTIMATED_MILEAGE_TO_HUB: estimated_mileage_to_hub,
            RunInfo.ESTIMATED_TIME_OF_HUB_ARRIVAL: copy(estimated_time_at_hub_arrival),
            RunInfo.MILES_FROM_PREVIOUS_WITH_HUB_INSERT: hub_insert_distance,
            RunInfo.DIFFERENCE: difference,
            RunInfo.IS_VALID_RUN_AT_LOCATION: requirements_met,
            RunInfo.OPTIMAL_HUB_DEPARTURE_TIME: copy(optimal_hub_departure_time),
            RunInfo.MINIMUM_OPTIMAL_TIME_AT_LOCATION: copy(minimum_optimal_start_time),
            RunInfo.ERROR_TYPE: error_type,
            RunInfo.ERROR_LOCATION: error_location
        }
    run.error_type = run_analysis_dict[(locations_visited[-2], locations_visited[-1])][RunInfo.ERROR_TYPE]
    run.error_location = run_analysis_dict[(locations_visited[-2], locations_visited[-1])][RunInfo.ERROR_LOCATION]
    return run_analysis_dict


def _check_requirements_met(run: RouteRun):
    """
    Checks if the requirements are met for each location in the route run.

    Args:
        run (RouteRun): The route run.

    Returns:
        None

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    for i, location in enumerate(run.ordered_route):
        if i == 0:
            continue
        previous_location = run.ordered_route[i - 1]
        if not run.run_analysis_dict[(previous_location, location)][RunInfo.IS_VALID_RUN_AT_LOCATION]:
            if run.run_analysis_dict[(previous_location, location)][RunInfo.ERROR_TYPE]:
                run.error_location = run.run_analysis_dict[(previous_location, location)][RunInfo.ERROR_LOCATION]
                run.error_type = run.run_analysis_dict[(previous_location, location)][RunInfo.ERROR_TYPE]
                break


def _check_optimal_return_to_hub(run: RouteRun):
    """
    Checks if there is an opportunity for the truck to return to the hub optimally.

    Args:
        run (RouteRun): The route run.

    Returns:
        None

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    if (run.package_total() + sum([len(location.package_set) for location in PackageHandler.all_locations
                                   if location.been_assigned]) != len(PackageHandler.all_packages)):
        for i, location in enumerate(run.ordered_route):
            if i == 0:
                continue
            previous_location = run.ordered_route[i - 1]
            mileage_difference = run.run_analysis_dict[(previous_location, location)][RunInfo.DIFFERENCE]
            packages_delivered = run.run_analysis_dict[(previous_location, location)][RunInfo.PACKAGES_DELIVERED]
            try:
                if (0 < mileage_difference <= config.HUB_RETURN_INSERTION_ALLOWANCE and len(packages_delivered) >=
                        len(PackageHandler.all_packages) % config.NUM_TRUCK_CAPACITY):
                    raise OptimalHubReturnError
            except OptimalHubReturnError:
                run.ordered_route = run.ordered_route[:i] + [Truck.hub_location]
                run.run_analysis_dict = _get_run_analysis_dict(run)
                run.locations = set(run.ordered_route)
                run.locations.remove(Truck.hub_location)
                run.error_type = OptimalHubReturnError
                run.error_location = (previous_location, location)
                break


def _analyze_run(run: RouteRun, truck: Truck):
    """
    Analyzes the route run and performs necessary optimizations and checks.

    Args:
        run (RouteRun): The route run.
        truck (Truck): The truck assigned to the route run.

    Returns:
        RouteRun: The analyzed route run.

    Time Complexity: O(n^2)
    Space Complexity: O(n)
    """

    run_analysis_dict = _get_run_analysis_dict(run)
    run.run_analysis_dict = run_analysis_dict
    if run.error_type and run.error_type is not LateDeliveryError:
        return run
    _optimized_revisit(run)
    _check_requirements_met(run)
    _check_optimal_return_to_hub(run)
    _simulate_load(run, truck)
    return run


def _simulate_load(run: RouteRun, truck: Truck):
    """
    Simulates the loading of packages onto the truck for the route run.

    Args:
        run (RouteRun): The route run.
        truck (Truck): The truck assigned to the route run.

    Returns:
        None

    Time Complexity: O(n * m)
    Space Complexity: O(n)
    """

    for location in run.ordered_route:
        if location.is_hub:
            continue
        for package in location.package_set:
            truck.add_package(package)
            if package.bundled_package_set:
                for bundle_package in package.bundled_package_set:
                    if not bundle_package.location.been_assigned:
                        truck.add_package(bundle_package)
    run.required_packages = truck.unload()


class RunPlanner:
    """
    A class that provides methods for planning and building route runs.

    Methods:
        build: Builds a route run based on the target location, truck, and other parameters.
    """

    @staticmethod
    def build(target_location, truck: Truck, run_focus: RunFocus = None, start_time=config.DELIVERY_DISPATCH_TIME):
        """
        Builds a route run based on the target location, truck, and other parameters.

        Args:
            target_location (Location or dict): The target location for the route run. Can be a single location or a
                dictionary containing paired target locations with their respective truck IDs.
            truck (Truck): The truck assigned to the route run.
            run_focus (RunFocus, optional): The run focus for the route run. Defaults to None.
            start_time (time, optional): The start time for the route run. Defaults to config.DELIVERY_DISPATCH_TIME.

        Returns:
            RouteRun or None: The constructed route run if successful, None if an error occurs.

        Time Complexity: O(n^2)
        Space Complexity: O(1)
        """

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
        run = _analyze_run(run, truck)
        if run.error_type and run.error_type is not OptimalHubReturnError:
            return run
        _set_locations_as_assigned(run)
        run.set_required_packages()
        run.set_estimated_mileage()
        run.set_estimated_completion_time()
        run.set_assigned_truck_id()
        truck.route_runs.append(run)
        return run
