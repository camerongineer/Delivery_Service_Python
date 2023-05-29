import random
from copy import copy
from datetime import time
from typing import List, Set

from src import config
from src.constants.color import Color
from src.constants.delivery_status import DeliveryStatus
from src.constants.run_info import RunInfo
from src.exceptions import AddressUpdateException, DelayedPackagesArrivedException
from src.models.package import Package
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.ui import UI
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder
from src.utilities.time_conversion import TimeConversion


def _display_package_load_message(truck: Truck, run: RouteRun, package_id: int):
    """
    Displays the message when a package is loaded onto a truck.

    Args:
        truck (Truck): The truck onto which the package is loaded.
        run (RouteRun): The current route run.
        package_id (int): The ID of the package being loaded.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    package = truck.get_package(package_id)
    UI.print(f'{truck.clock} | Package #{str(package_id).zfill(2)} | Destination: "{package.location.name}" | Loaded '
             f'successfully onto Truck #{truck.truck_id} | '
             f'Packages currently loaded: {len(truck)} / {config.NUM_TRUCK_CAPACITY}' +
             ('\n** WILL NOT BE DELIVERED UNTIL AFTER RELOADING BUT IS REQUIRED TO BE CARRIED **'
              if package.location not in run.ordered_route else ''), sleep_seconds=2, color=Color.YELLOW)


def _display_awaiting_package_message(truck: Truck, package: Package):
    """
    Displays the message when a truck is awaiting a package to arrive at the hub.

    Args:
        truck (Truck): The truck awaiting the package.
        package (Package): The package being awaited.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} awaiting on Package #{package.package_id} to arrive at the hub',
             sleep_seconds=2, color=Color.RED)


def _display_initial_truck_loading_message():
    """
    Displays the message indicating the commencement of truck loading.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'Truck loading commencing at {config.STANDARD_PACKAGE_LOAD_START_TIME}',
             think=True, color=Color.YELLOW)


def _display_next_location(truck: Truck):
    """
    Displays the message indicating the truck's departure to the next location.

    Args:
        truck (Truck): The truck departing.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} leaving {truck.current_location.name} and '
             f'heading to {truck.next_location.name} at {truck.next_location.get_full_address()}',
             think=True)


def _display_delivery_info(truck: Truck, delivered_packages: Set[Package]):
    """
    Displays the delivery information for a truck.

    Args:
        truck (Truck): The truck delivering packages.
        delivered_packages (Set[Package]): The set of delivered packages.

    Time Complexity: O(n)
    Space Complexity: O(n)
    """

    analysis_dict = truck.current_run.run_analysis_dict[(truck.previous_location, truck.current_location)]
    total_undelivered = ([package for package in PackageHandler.all_packages
                         if package.status is not DeliveryStatus.DELIVERED])
    UI.print(f'{truck.clock} | Truck #{truck.truck_id} | Current mileage:'
             f' {analysis_dict[RunInfo.ESTIMATED_MILEAGE]:.1f} | Packages have been delivered to'
             f' "{truck.current_location.name}" | {len(delivered_packages)} delivered, '
             f'{analysis_dict[RunInfo.UNDELIVERED_PACKAGES_TOTAL]} remaining on truck | '
             f'{(len(total_undelivered))} / {len(PackageHandler.all_packages)} total remaining',
             sleep_seconds=3, color=UI.ASSIGNED_COLOR[truck.truck_id])


def _display_reload_info(truck: Truck):
    """
    Displays information about the truck's arrival at a location for reload.

    Args:
        truck (Truck): The truck that has arrived for reload.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} has arrived at {truck.current_location.name} for reload |'
             f' Total Run Mileage: {truck.current_run.estimated_mileage:.1f}',
             sleep_seconds=4, color=Color.MAGENTA)


def _display_route_completion(truck: Truck):
    """
    Displays information about the completion of the truck's route.

    Args:
        truck (Truck): The truck that has completed the route.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} arrived at {truck.current_location.name} for final delivery |'
             f' {len(truck.current_location.package_set)} total delivered | Route completed successfully ! |'
             f' Total Run Mileage: {truck.current_run.estimated_mileage:.1f}',
             sleep_seconds=4, color=UI.ASSIGNED_COLOR[truck.truck_id])


def _reload_for_next_run(truck: Truck, run: RouteRun, fast_reload=False):
    """
    Reloads the truck for the next run.

    Args:
        truck (Truck): The truck to reload.
        run (RouteRun): The current route run.
        fast_reload (bool): Flag indicating whether to perform a fast reload (without simulated loading time).

    Time Complexity: O(n^2)
    Space Complexity: O(n)
    """

    for package in sorted(list(run.required_packages), key=lambda _package: _package.package_id):
        if truck.is_package_on_truck(package):
            continue
        if package.status is DeliveryStatus.AT_HUB:
            truck.add_package(package, False)
            if not fast_reload:
                DeliveryRunner.global_clock = TimeConversion.increment_time(
                    DeliveryRunner.global_clock, random.randint(package.weight,
                                                                config.PACKAGE_LOAD_SPEED_MAX_SECONDS))
                truck.set_clock(DeliveryRunner.global_clock)
            _display_package_load_message(truck, run, package.package_id)
    unloaded_packages = set([package for package in run.required_packages
                             if package.status == DeliveryStatus.ON_ROUTE_TO_DEPOT])
    for package in unloaded_packages:
        _display_awaiting_package_message(truck, package)


def _display_address_update_message(address_update_message: str):
    """
    Displays a message for an address update.

    Args:
        address_update_message (str): The address update message to display.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{DeliveryRunner.global_clock} | {address_update_message}', color=Color.RED, sleep_seconds=3)


def _display_delayed_packages_arrival_message():
    """
    Displays a message indicating that delayed packages have arrived and are available to be loaded.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{DeliveryRunner.global_clock} | Delayed packages have arrived and are available to be loaded',
             color=Color.GREEN, sleep_seconds=3)


def _display_returned_to_visited_location_message(truck: Truck):
    """
    Displays a message indicating that the truck has returned to a visited location for mileage optimization.

    Args:
        truck (Truck): The truck that returned.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} returned to {truck.current_location.name}'
             f' for mileage optimization purposes | No packages delivered', think=True, color=Color.BLUE)


def _display_starting_route_message(truck: Truck):
    """
    Displays a message indicating that a truck is beginning its route.

    Args:
        truck (Truck): The truck that is beginning its route.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    UI.print(f'{truck.clock} | Truck #{truck.truck_id} beginning route',
             think=True, color=UI.ASSIGNED_COLOR[truck.truck_id])
    truck.dispatch()
    _display_next_location(truck)


def _display_deliveries_commencing_message(start_time: time):
    """
    Displays a message indicating that deliveries are commencing.

    Args:
        start_time (time): The start time of the deliveries.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print('Deliveries commencing', think=True, color=Color.MAGENTA)
    UI.print(f'\nThe time is now {UI.UNDERLINE}{start_time}{Color.COLOR_ESCAPE.value}',
             sleep_seconds=3, extra_lines=1)


def _get_important_status_update_times():
    """
    Retrieves the important status update times.

    Returns:
        list: A time-sorted list of important status update times.

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """

    important_update_times = list(PackageHandler.get_all_expected_status_update_times())
    important_update_times += [times['update_time'] for times in config.EXCEPTED_UPDATES.values()]
    important_update_times.sort()
    return important_update_times


def _display_route_completion_message(completion_time):
    """
    Displays a message indicating the successful completion of all routes.

    Args:
        completion_time: The completion time of all routes.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    total_mileage = sum([run.estimated_mileage for run in DeliveryRunner.route_runs])
    UI.print(f'\nAll routes completed successfully, and all packages were delivered! |'
             f' Total mileage: {total_mileage:.1f} | Completion time: {completion_time}',
             color=Color.BRIGHT_GREEN)


class DeliveryRunner:
    """
    Class responsible for loading trucks, commencing deliveries, and managing the delivery process.

    Attributes:
        global_clock (time): The current global time.
        trucks (Set[Truck]): Set of trucks available for deliveries.
        route_runs (Set[RouteRun]): Set of route runs to be completed.
    """

    global_clock: time = config.STANDARD_PACKAGE_LOAD_START_TIME
    trucks: Set[Truck] = set()
    route_runs: Set[RouteRun] = set()

    @staticmethod
    def load_trucks():
        """
        Loads the trucks with packages for delivery.

        Time Complexity: O(n^2)
        Space Complexity: O(n)
        """

        trucks: List[Truck] = list(RouteBuilder.build_optimized_runs())
        _display_initial_truck_loading_message()
        unused_trucks = [truck for truck in trucks if not truck.route_runs]
        for unused_truck in unused_trucks:
            UI.print(f'Truck #{unused_truck.truck_id} not needed today. Will remain at hub facility', think=True)
        print('\n\n')
        runs: List[RouteRun] = [run for truck in trucks for run in truck.route_runs]
        runs.sort()
        for run in runs:
            truck = [truck for truck in trucks if truck.truck_id == run.assigned_truck_id][0]
            if truck.is_loaded():
                continue
            truck.set_clock(DeliveryRunner.global_clock)
            UI.print(f'Loading Truck #{truck.truck_id}', think=True, extra_lines=1,
                     color=UI.ASSIGNED_COLOR[truck.truck_id])
            _reload_for_next_run(truck, run)
            print('\n\n')
        DeliveryRunner.trucks = set(trucks)
        DeliveryRunner.route_runs = set(runs)
        UI.print('Initial truck loading complete', color=Color.GREEN, sleep_seconds=2, extra_lines=2)

    @staticmethod
    def commence_deliveries():
        """
        Commences the package deliveries.

        Time Complexity: O(n^2)
        Space Complexity: O(n)
        """

        # Determines the start and completion times for the deliveries.
        start_time = min([run.start_time for run in DeliveryRunner.route_runs])
        completion_time = max([run.estimated_completion_time for run in DeliveryRunner.route_runs])

        # Initializes the global clock with the start time.
        DeliveryRunner.global_clock = copy(start_time)
        _display_deliveries_commencing_message(start_time)

        # Creates a list of important status update times.
        important_update_times = _get_important_status_update_times()

        visited_locations = set()
        while DeliveryRunner.route_runs and (DeliveryRunner.global_clock <= completion_time):
            important_time = None
            if important_update_times and DeliveryRunner.global_clock == important_update_times[0]:
                important_time = important_update_times.pop(0)
            for truck in copy(DeliveryRunner.trucks):
                truck.set_clock(DeliveryRunner.global_clock)
                run: RouteRun = truck.current_run

                # Status update is performed if there is an expected important update.
                if important_time:
                    try:
                        PackageHandler.bulk_status_update(DeliveryRunner.global_clock)
                    except AddressUpdateException as address_update_exception:
                        _display_address_update_message(address_update_exception.message)
                    except DelayedPackagesArrivedException:
                        _display_delayed_packages_arrival_message()
                        for truck_at_hub in DeliveryRunner.trucks:
                            truck_at_hub.set_clock(DeliveryRunner.global_clock)
                            if truck_at_hub.current_location.is_hub and truck_at_hub.current_run:
                                _reload_for_next_run(truck_at_hub, truck_at_hub.current_run, fast_reload=True)

                # Truck continues deliveries until all locations of the ordered route are complete
                if run and (run.start_time <= truck.clock):
                    analysis_dict = run.run_analysis_dict[(truck.previous_location, truck.current_location)]
                    time_at_next = analysis_dict[RunInfo.ESTIMATED_TIME_AT_NEXT]
                    if run and truck.clock == run.start_time:
                        _display_starting_route_message(truck)

                    # Truck makes delivery upon arrive at next location or completes route run
                    if time_at_next == DeliveryRunner.global_clock:
                        truck.previous_location = truck.current_location
                        truck.current_location = truck.next_location
                        del run.ordered_route[0]
                        if not run.ordered_route:
                            if not truck.route_runs:
                                truck.deliver()
                                _display_route_completion(truck)
                                truck.current_run = None
                                truck.previous_location = None
                                truck.next_location = None
                            elif truck.current_location.is_hub and truck.route_runs:
                                truck.previous_location = None
                                truck.route_runs.sort()
                                _display_reload_info(truck)
                                truck.current_run = truck.route_runs.pop(0)
                                del truck.current_run.ordered_route[0]
                                truck.next_location = truck.current_run.ordered_route[0]
                                _reload_for_next_run(truck, truck.current_run)
                            continue

                        if not truck.current_location.is_hub and truck.current_location in visited_locations:
                            _display_returned_to_visited_location_message(truck)
                        else:
                            visited_locations.add(truck.current_location)
                            delivered_packages = truck.deliver()
                            _display_delivery_info(truck, delivered_packages)
                        truck.next_location = run.ordered_route[0]
                        _display_next_location(truck)
                    elif (TimeConversion.seconds_between_times(start_time, DeliveryRunner.global_clock)
                          % (750 // truck.truck_id) == 0):
                        UI.print(f'{truck.clock} | Truck #{truck.truck_id} traveling', think=True)
                elif truck.route_runs:

                    # Truck begins a route run if it has one to start if it's the start time
                    for i in range(len(sorted(truck.route_runs))):
                        if TimeConversion.is_time_at_or_before_other_time(truck.clock, truck.route_runs[i].start_time):
                            truck.current_run = truck.route_runs.pop(i)
                            truck.current_location = truck.current_run.ordered_route[0]
                            truck.next_location = truck.current_run.ordered_route[1]
                            if truck.current_run.start_time == truck.clock:
                                _display_starting_route_message(truck)
                            visited_locations.add(truck.current_location)
                            del truck.current_run.ordered_route[0]
                            break
                elif run:
                    continue
                else:
                    DeliveryRunner.trucks.remove(truck)
            DeliveryRunner.global_clock = TimeConversion.increment_time(DeliveryRunner.global_clock, time_seconds=1)

        if len([package for package in PackageHandler.all_packages if package.status != DeliveryStatus.DELIVERED]) == 0:
            _display_route_completion_message(completion_time)

        UI.press_enter_to_continue(simulation_end=True)
