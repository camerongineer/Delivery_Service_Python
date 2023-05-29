import random
from copy import copy
from typing import Set

from src import config
from src.constants.color import Color
from src.constants.run_focus import RunFocus
from src.constants.run_info import RunInfo
from src.exceptions.route_builder_error import OptimalHubReturnError, UnconfirmedPackageDeliveryError
from src.models.location import Location
from src.models.package import Package
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.run_planner import RunPlanner
from src.utilities.time_conversion import TimeConversion
from src.ui import UI

__all__ = ['RouteBuilder']


def _display_package_details(in_package: Package):
    """
    Displays the details of a package.

    Args:
        in_package (Package): The package to display the details for.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print((f'Package ID: {str(in_package.package_id).zfill(2)} | ' + f'Arrival time at hub: '
              f'{in_package.hub_arrival_time}  | ' +
              (f'Has a deadline of {in_package.deadline}'
               if in_package.deadline != config.DELIVERY_RETURN_TIME else'Has no deadline') +
              (f' | Address is not confirmed. The expected update time of confirmation is'
               f' {config.EXCEPTED_UPDATES[in_package.package_id]["update_time"]}'
               if not in_package.is_verified_address else '')), sleep_seconds=1)


def _display_location_details(in_location: Location, origin_location: Location):
    """
    Displays the details of a location.

    Args:
        in_location (Location): The location to display the details for.
        origin_location (Location): The origin location for the distance calculation.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    package_total = len(in_location.package_set)
    UI.print(f'"{in_location.name}" at "{in_location.get_full_address()}" found', 2, color=Color.BLUE)
    UI.print(f'{package_total} package' + ('s are ' if package_total != 1 else " is ") +
             'due to be delivered to this location', 2)
    UI.print(f'From "{origin_location.name}" at "{origin_location.get_full_address()} to '
             f'"{in_location.name}" at "{in_location.get_full_address()} is {in_location.distance(origin_location):.1f}'
             f' miles', sleep_seconds=4, extra_lines=1)


def _find_most_spread_out_location() -> Location:
    """
    Finds the location that is the most spread out from others.

    Returns:
        Location: The most spread out location.

    Time Complexity: O(n log n)
    Space Complexity: O(1)
    """

    UI.print('Searching for location that is the most spread out from others', color=Color.YELLOW, think=True)
    most_spread_out_location = (sorted(PackageHandler.all_locations,
                                       key=lambda location: sum(location.distance_dict.values())).pop())
    _display_location_details(most_spread_out_location, Truck.hub_location)
    return most_spread_out_location


def _find_earliest_deadline_packages() -> Location:
    """
    Finds the location with the earliest deadline packages.

    Returns:
        Location: The location with the earliest deadline packages.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

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
    """
    Finds the location that is furthest away from a given location.

    Args:
        in_location (Location): The location to find the furthest location away from.

    Returns:
        Location: The furthest location from the given location.

    Time Complexity: O(n log n)
    Space Complexity: O(1)
    """

    UI.print(f'Searching for location furthest away from "{in_location.name}"', color=Color.YELLOW, think=True)
    distance_sorted_locations = sorted(in_location.distance_dict.items(), key=lambda item: item[1], reverse=True)
    furthest_location = distance_sorted_locations[0][0]
    _display_location_details(furthest_location, in_location)
    return furthest_location


def _calculate_best_targets():
    """
    Calculates the best target locations for the deliveries.

    Returns:
        list: The list of best target locations.

    Time Complexity: O(n log n)
    Space Complexity: O(1)
    """

    best_targets = []
    package_total = len(PackageHandler.all_packages)
    truck_capacity = config.NUM_TRUCK_CAPACITY
    minimum_runs = int(package_total / config.NUM_TRUCK_CAPACITY)
    if package_total % config.NUM_TRUCK_CAPACITY:
        minimum_runs += 1
    UI.print(f'\n\n{package_total} packages detected, truck capacity is {truck_capacity}', sleep_seconds=2)
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


def _analyze_best_targets(best_targets):
    """
    Analyzes the best target locations and recommends grouping locations assigned to the same truck on the same run if applicable.

    Args:
        best_targets (list): The list of best target locations.

    Returns:
        list: The remaining targets after the analysis.

    Time Complexity: O(n log n)
    Space Complexity: O(1)
    """

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


def _analyze_paired_targets(index_number: int, paired_targets: dict):
    """
    Analyzes the paired targets for a specific run and provides recommendations.

    Args:
        index_number (int): The index number of the run.
        paired_targets (dict): A dictionary containing the truck ID as the key and the set of targets as the value.

    Returns:
        RunFocus: The recommended run focus based on the analysis.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    truck_id, target_set = copy(paired_targets).popitem()
    UI.print(f'Analyzing {len(target_set)} targets for run #{index_number + 1} - '
             f'"{list(target_set)[0].name}" and "{list(target_set)[1].name}"', color=Color.YELLOW, think=True)
    if truck_id:
        UI.print(f'These locations are both assigned to truck #{truck_id}', color=Color.RED, think=True)
        if len([location for location in PackageHandler.all_locations if location.assigned_truck_id == truck_id]) >= 4:
            UI.print(f'Prioritizing run focused on deliveries to locations requiring truck #{truck_id}',
                     think=True, extra_lines=2)
            UI.print(f'Multiple locations requiring truck #{truck_id} detected', sleep_seconds=4, color=Color.RED)
    return RunFocus.ASSIGNED_TRUCK


def _analyze_target_location(index_number: int, target_location: Location):
    """
    Analyzes a target location and provides recommendations based on its attributes.

    Args:
        index_number (int): The index number of the target location.
        target_location (Location): The target location to analyze.

    Returns:
        RunFocus: The recommended run focus based on the analysis.


    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'Analyzing target #{index_number + 1} - "{target_location.name}"', color=Color.YELLOW, think=True,
             extra_lines=1)
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
    """
    Initializes the delivery trucks for the simulation.

    Args:
        required_truck_ids (Set[int]): The set of required truck IDs.
        number_of_delivery_trucks (int): The total number of delivery trucks.

    Returns:
        Tuple[Set[Truck], Set[Truck]]: A tuple containing the available trucks and unavailable trucks.

    Time Complexity: O(n * m)
    Space Complexity: O(n)
    """

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
    """
    Displays a message indicating the optimal time to return to the hub to reload more packages.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print('Detected optimal time to return to hub to reload more packages',
             sleep_seconds=4, color=Color.GREEN)
    UI.print(f'Recommending truck returns to hub between deliveries', think=True, extra_lines=2)


def _unconfirmed_package_delivery_message():
    """
    Displays a message indicating the delivery of an unconfirmed package.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print('Detected a delivery of an unconfirmed package, a time is known for expected confirmation',
             sleep_seconds=4, color=Color.RED)
    UI.print(f'Recommending truck departs at later time to accommodate', think=True)
    UI.print(f'Restarting run creation with new start time', think=True, extra_lines=2)


def _analyze_route_run(index_number: int, run: RouteRun):
    """
       Analyzes a route run and provides information about the run and its locations.

       Args:
           index_number (int): The index number of the route run.
           run (RouteRun): The route run to analyze.

       Time Complexity: O(n)
       Space Complexity: O(n)
    """

    UI.print(f'Run #{index_number + 1} successfully built!', sleep_seconds=3, extra_lines=1, color=Color.YELLOW)
    UI.print(f'Truck #{run.assigned_truck_id} is assigned, with an estimated departure time of {run.start_time}'
             f' and completion time of {run.estimated_completion_time}', extra_lines=1, sleep_seconds=3)
    UI.print(f'Analysing run #{index_number + 1} with target location: "{run.target_location.name}"',
             think=True, extra_lines=1)
    visited_locations = list()
    for i, location in enumerate(run.ordered_route):
        if location.is_hub:
            visited_locations.append(location)
            continue
        location_dict = run.run_analysis_dict[(visited_locations[-1], location)]
        if location in visited_locations:
            UI.print(f'Expected arrival time is {location_dict[RunInfo.ESTIMATED_TIME]} | ' +
                     f'Mileage from the previous location is '
                     f'{location_dict[RunInfo.PREVIOUS_LOCATION].distance(location)} miles | '
                     f'Estimated total mileage at this location is {location_dict[RunInfo.ESTIMATED_MILEAGE]:.1f}'
                     f'\nReturning to {location.name} to minimize mileage | No packages delivered',
                     color=Color.RED, sleep_seconds=3, extra_lines=1)
        else:
            UI.print((f'Expected arrival time is {location_dict[RunInfo.ESTIMATED_TIME]} | '
                      f'Mileage from the previous location is '
                      f'{location_dict[RunInfo.PREVIOUS_LOCATION].distance(location)} miles | '
                      f'Estimated total mileage at this location is {location_dict[RunInfo.ESTIMATED_MILEAGE]:.1f}'),
                     sleep_seconds=1, color=Color.BLUE)
            packages = location.package_set
            UI.print(f'{len(packages)} package' + ('s' if len(packages) != 1 else '') +
                     f' | "{location.name}" located at "{location.get_full_address()}"',
                     sleep_seconds=1, color=Color.BLUE)
            for package in packages:
                _display_package_details(package)
            print()
        visited_locations.append(location)
    if run.ordered_route[-1].is_hub:
        UI.print(f'Expected arrival back at the hub is {run.estimated_completion_time}',
                 extra_lines=1, color=Color.YELLOW, sleep_seconds=3)
        undelivered_packages = (run.required_packages.difference(
            set.union(*[location.package_set for location in run.ordered_route])))
        if undelivered_packages:
            UI.print('These packages must remain on the truck during reload for the next run',
                     color=Color.RED, sleep_seconds=4, extra_lines=1)
            for package in undelivered_packages:
                _display_package_details(package)
            print()
    UI.print(f'\nThe total expected miles on this run is {run.estimated_mileage:.1f} '
             f'with an expected completion time of {run.estimated_completion_time} |'
             f' The expected package delivery total is {run.package_total()}',
             sleep_seconds=7, color=Color.GREEN, extra_lines=3)


def _select_truck_for_run(target_location: Location, available_truck_pool: Set[Truck],
                          unavailable_truck_pool: Set[Truck]) -> Truck:
    """
       Selects a truck for a run based on the target location and the available and unavailable truck pools.

       Args:
           target_location (Location): The target location for the run.
           available_truck_pool (Set[Truck]): The set of available trucks.
           unavailable_truck_pool (Set[Truck]): The set of unavailable trucks.

       Returns:
           Truck: The selected truck for the run.

       Time Complexity: O(n)
       Space Complexity: O(1)
       """

    truck = None
    if (len([package for package in PackageHandler.all_packages if not package.location.been_assigned])
            <= config.NUM_TRUCK_CAPACITY):
        remaining_ids = set([package.assigned_truck_id for package in PackageHandler.all_packages
                             if package.assigned_truck_id and not package.location.been_assigned])
        target_location.assigned_truck_id = remaining_ids.pop()
    for available_truck in copy(available_truck_pool):
        if (isinstance(target_location, Location) and (target_location.has_required_truck_package or
                                                       target_location.assigned_truck_id)):
            if target_location.assigned_truck_id and available_truck.truck_id == target_location.assigned_truck_id:
                truck = available_truck
        elif isinstance(target_location, dict):
            truck_id, target_set = copy(target_location).popitem()
            if truck_id == available_truck.truck_id:
                truck = available_truck
        else:
            truck = random.choice(list(available_truck_pool))
            break
    if truck:
        available_truck_pool.remove(truck)
        unavailable_truck_pool.add(truck)
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


def _get_unassigned_locations():
    """
    Retrieves the set of unassigned locations.

    Returns:
        Set[Location]: The set of unassigned locations.

    Notes:
        - Retrieves the set of locations that have not been assigned yet.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    return set([location for location in PackageHandler.all_locations if not location.been_assigned])


def _create_optimized_runs(targets) -> Set[Truck]:
    """
    Creates optimized runs based on the target locations.

    Args:
        targets: The target locations for the runs.

    Returns:
        Set[Truck]: The set of trucks assigned to the runs.

    Time Complexity: O(n * m)
    Space Complexity: O(n)
    """

    required_truck_ids = set([pair.keys() for pair in targets if isinstance(pair, dict)].pop())
    UI.print('Finding available delivery trucks', think=True, color=Color.YELLOW)
    available_truck_pool, unavailable_truck_pool = _initialize_trucks(required_truck_ids)
    UI.print(f'{len(available_truck_pool.union(unavailable_truck_pool))} trucks found', sleep_seconds=4, extra_lines=1)
    run_set = set()
    for i, target_location in enumerate(targets):
        run = None
        truck = None
        focus_type = None
        try:
            if isinstance(target_location, dict):
                focus_type = _analyze_paired_targets(i, target_location)
            else:
                focus_type = _analyze_target_location(i, target_location)
            truck = _select_truck_for_run(target_location, available_truck_pool, unavailable_truck_pool)
            created_run = RunPlanner.build(target_location, truck, focus_type)
            if created_run.error_type:
                run = created_run
                raise created_run.error_type
            else:
                run = created_run
        except OptimalHubReturnError:
            _optimal_hub_return_message()
        except UnconfirmedPackageDeliveryError:
            _unconfirmed_package_delivery_message()
            error_run_start_time = run.run_analysis_dict[run.error_location][RunInfo.OPTIMAL_HUB_DEPARTURE_TIME]
            modified_error_start_time = TimeConversion.increment_time(error_run_start_time, time_seconds=-120)
            run = RunPlanner.build(target_location, truck, focus_type, start_time=modified_error_start_time)
        finally:
            _analyze_route_run(i, run)
            run_set.update(set(truck.route_runs))
            UI.press_enter_to_continue()
    if not _get_unassigned_locations():
        UI.print('Route plan built successfully, all packages have been accounted for and meet all time constants',
                 color=Color.GREEN, sleep_seconds=3, extra_lines=1)
        total_mileage = sum([run.estimated_mileage for run in run_set])
        latest_time = max([run.estimated_completion_time for run in run_set])
        UI.print(f'All deliveries expected to be completed by {latest_time} with a total mileage of {total_mileage:.1f}'
                 , extra_lines=1, sleep_seconds=3)
        UI.print('Continuing to "Deliveries" phase', color=Color.YELLOW, think=True, extra_lines=3)
    return available_truck_pool.union(unavailable_truck_pool)


class RouteBuilder:

    @staticmethod
    def build_optimized_runs():
        """
        Builds optimized runs based on the best targets.

        Returns:
            Set[Truck]: The set of trucks assigned to the runs.

        Time Complexity: O(n * m)
        Space Complexity: O(n)
        """

        best_targets = _calculate_best_targets()
        assigned_trucks = _create_optimized_runs(best_targets)
        return assigned_trucks
