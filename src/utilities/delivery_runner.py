import random
from copy import copy
from time import sleep, time
from typing import List, Set

from src import config
from src.constants.color import Color
from src.constants.delivery_status import DeliveryStatus
from src.constants.run_info import RunInfo
from src.models.location import Location
from src.models.package import Package
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.ui import UI
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder
from src.utilities.time_conversion import TimeConversion


def _display_package_load_message(truck: Truck, run: RouteRun, package_id: int):
    package = truck.get_package(package_id)
    UI.print(f'{truck.clock} | Package #{str(package_id).zfill(2)} | Destination: "{package.location.name}" at '
             f'"{package.location.get_full_address()}" | Loaded successfully onto Truck #{truck.truck_id}' +
             ('\n** WILL NOT BE DELIVERED UNTIL AFTER RELOADING BUT IS REQUIRED TO BE CARRIED **\n'
              if package.location not in run.ordered_route else ''), sleep_seconds=2)


def _display_initial_truck_loading_message():
    UI.print(f'Truck loading commencing at {config.STANDARD_PACKAGE_LOAD_START_TIME}',
             think=True, color=Color.YELLOW, extra_lines=2)


def _display_next_location(truck: Truck):
    UI.print(f'\n{truck.clock} | Leaving {truck.current_location.name} and heading to {truck.next_location.name} '
             f'at {truck.next_location.get_full_address()}', think=True, color=Color.YELLOW)


def _display_delivery_info(truck: Truck, delivered_packages: Set[Package]):
    analysis_dict = truck.current_run.run_analysis_dict[truck.current_location]
    UI.print(f'\n{truck.clock} | Current mileage: {analysis_dict[RunInfo.ESTIMATED_MILEAGE]} | Packages have been'
             f' delivered to "{truck.current_location.name}" | {len(delivered_packages)} total',
             sleep_seconds=3, color=Color.GREEN)


def _display_reload_info(truck):
    UI.print(f'Arrived at {truck.current_location.name} for reload, awaiting delayed packages', think=True)


def _display_route_completion(truck):
    UI.print(f'{truck.clock} | Truck #{truck.truck_id} Route successfully completed!',
             sleep_seconds=4, color=Color.GREEN)


class DeliveryRunner:

    global_clock: time = config.STANDARD_PACKAGE_LOAD_START_TIME
    trucks: Set[Truck] = set()
    route_runs: Set[RouteRun] = set()

    @staticmethod
    def load_trucks():
        trucks: List[Truck] = RouteBuilder.build_optimized_runs()
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
            UI.print(f'Loading Truck #{truck.truck_id}', think=True, extra_lines=1, color=Color.BLUE)
            for package in sorted(list(run.required_packages), key=lambda _package: _package.package_id):
                if package.status is DeliveryStatus.AT_HUB:
                    truck.add_package(package)
                    DeliveryRunner.global_clock = TimeConversion.increment_time(
                        DeliveryRunner.global_clock, random.randint(package.weight,
                                                                    config.PACKAGE_LOAD_SPEED_MAX_SECONDS))
                    truck.set_clock(DeliveryRunner.global_clock)
                    package.update_status(DeliveryStatus.LOADED, DeliveryRunner.global_clock)
                    _display_package_load_message(truck, run, package.package_id)
            unloaded_packages = set([package for package in run.required_packages
                                     if package.status == DeliveryStatus.ON_ROUTE_TO_DEPOT])
            for package in unloaded_packages:
                UI.print(f'Awaiting on Package #{package.package_id} to arrive at the hub', sleep_seconds=2,
                         color=Color.RED)
            print('\n\n')
        DeliveryRunner.trucks = set(trucks)
        DeliveryRunner.route_runs = set(runs)
        UI.print('Initial truck loading complete', color=Color.GREEN, sleep_seconds=2, extra_lines=2)

    @staticmethod
    def commence_deliveries():
        config.UI_ENABLED = True
        config.UI_ELEMENTS_ENABLED = False
        start_time = min([run.start_time for run in DeliveryRunner.route_runs])
        completion_time = max([run.estimated_completion_time for run in DeliveryRunner.route_runs])
        DeliveryRunner.global_clock = copy(start_time)
        UI.print('Deliveries commencing', think=True, color=Color.MAGENTA)
        UI.print(f'\nThe time is now {UI.UNDERLINE}{start_time}{Color.COLOR_ESCAPE.value}',
                 sleep_seconds=3, extra_lines=1)
        visited_locations = set()
        important_update_times = PackageHandler.get_all_expected_status_update_times()
        important_update_times.add(config.PACKAGE_9_ADDRESS_CHANGE_TIME)
        while DeliveryRunner.route_runs and (DeliveryRunner.global_clock <= completion_time):
            for truck in copy(DeliveryRunner.trucks):
                truck.set_clock(DeliveryRunner.global_clock)
                if truck.current_run:
                    run: RouteRun = truck.current_run
                    if truck.current_location.is_hub:
                        time_at_next = run.run_analysis_dict[truck.next_location][RunInfo.ESTIMATED_TIME]
                    else:
                        time_at_next = run.run_analysis_dict[truck.current_location][RunInfo.ESTIMATED_TIME_AT_NEXT]

                    if time_at_next == DeliveryRunner.global_clock:
                        truck.previous_location = truck.current_location
                        truck.current_location = truck.next_location
                        if not truck.current_location.is_hub:
                            visited_locations.add(truck.current_location)
                        del run.ordered_route[0]
                        if not run.ordered_route:
                            if not truck.route_runs:
                                _display_route_completion(truck)
                            elif truck.current_location.is_hub:
                                _display_reload_info(truck)
                            truck.current_run = None
                            truck.next_location = None
                            continue
                        truck.next_location = run.ordered_route[0]
                        delivered_packages = truck.deliver()
                        _display_delivery_info(truck, delivered_packages)
                        _display_next_location(truck)
                        continue
                    if TimeConversion.seconds_between_times(start_time, DeliveryRunner.global_clock) % 300 == 0:
                        UI.print(f'Truck #{truck.truck_id} traveling | {truck.clock}', think=True)
                elif truck.route_runs:
                    for i in range(len(copy(truck.route_runs))):
                        if truck.route_runs[i].start_time == truck.clock:
                            truck.current_run = truck.route_runs.pop(i)
                            UI.print(f'{truck.clock} | Truck #{truck.truck_id} beginning route',
                                     think=True, color=Color.GREEN)
                            truck.current_location = truck.current_run.ordered_route[0]
                            truck.next_location = truck.current_run.ordered_route[1]
                            del truck.current_run.ordered_route[0]
                            _display_next_location(truck)
                            break
                else:
                    DeliveryRunner.trucks.remove(truck)
            DeliveryRunner.global_clock = TimeConversion.increment_time(DeliveryRunner.global_clock, time_seconds=1)
            if any(DeliveryRunner.global_clock == update_time for update_time in important_update_times):
                PackageHandler.bulk_status_update(DeliveryRunner.global_clock)



