from copy import copy
from datetime import time
from typing import List, Set

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash
from src.utilities.time_conversion import TimeConversion

__all__ = ['PackageHandler']


def _is_loadable_package_set(truck: Truck, in_package_set: Set[Package]) -> bool:
    for in_package in in_package_set:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
        if in_package.assigned_truck_id and in_package.assigned_truck_id != truck.truck_id:
            return False
    return True


def _is_package_arriving_at_hub(package: Package, current_time: time) -> bool:
    return package.status is DeliveryStatus.ON_ROUTE_TO_DEPOT and \
        TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time)


def _is_package_address_updating(package: Package, current_time: time) -> bool:
    return TimeConversion.is_time_at_or_before_other_time(config.PACKAGE_9_ADDRESS_CHANGE_TIME, current_time) and \
        not package.is_verified_address


class PackageHandler:
    all_locations = CsvParser.initialize_locations()
    all_packages = CsvParser.initialize_packages(all_locations)
    package_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
    package_hash.add_all_packages(all_packages)
    Truck.hub_location = [location for location in all_locations if location.is_hub][0]
    today_special_times = {config.PACKAGE_9_ADDRESS_CHANGE_TIME}

    @staticmethod
    def load_packages(truck: Truck, package_sets: List[Set[Package]]):
        for package_set in package_sets:
            if truck.current_location is not Truck.hub_location or not _is_loadable_package_set(truck, package_set):
                return False
        for package_set in package_sets:
            for package in package_set:
                package.update_status(DeliveryStatus.LOADED, truck.clock)
                truck.add_package(package)
            return True

    @staticmethod
    def update_delivery_location(locations_list: List[Location], package: Package, updated_address: str):
        try:
            address, city, state_zip = updated_address.split(', ')
            zip_code = int(state_zip.split(' ')[1])
            for location in locations_list:
                if str(address).startswith(location.address) and location.zip_code == zip_code:
                    old_location = package.location
                    old_location.package_set.remove(package)
                    package.location = location
                    package.location.package_set.add(package)
                    package.is_verified_address = True
                    return True
        except (ValueError, TypeError):
            return False
        return False

    @staticmethod
    def bulk_status_update(current_time: time, packages=all_packages):
        for package in packages:
            if _is_package_arriving_at_hub(package, current_time):
                package.update_status(DeliveryStatus.AT_HUB, current_time)
            if _is_package_address_updating(package, current_time):
                old_location = package.location.address
                PackageHandler.update_delivery_location(PackageHandler.all_locations, package,
                                                        config.PACKAGE_9_UPDATED_ADDRESS)
                new_location = package.location.address
                print(
                    f'Package: {package.package_id:02} address changed from "{old_location}" to "{new_location} at {current_time}"')

    @staticmethod
    def get_location_package_dict(in_packages=all_packages):
        location_package_dict = dict()
        for package in in_packages:
            if package.location not in location_package_dict:
                location_package_dict[package.location] = set()
            location_package_dict[package.location].add(package)
        return location_package_dict

    @staticmethod
    def get_location_packages(location: Location, in_packages=all_packages) -> Set[Package]:
        if location not in PackageHandler.get_location_package_dict(in_packages).keys():
            return set()
        return PackageHandler.get_location_package_dict(in_packages)[location]

    @staticmethod
    def is_delivered_on_time(current_time: time, packages: Set[Package]):
        for package in packages:
            if not TimeConversion.is_time_at_or_before_other_time(current_time, package.deadline):
                print(f'Package id{package.package_id} was delivered late at {current_time}')

    @staticmethod
    def get_bundled_packages(locations=all_locations, all_location_packages=False, ignore_assigned=False) -> Set[Package]:
        package_bundle_set = set()
        for location in locations:
            if location.has_bundled_package:
                for package in location.package_set:
                    if package.bundled_package_set:
                        package_bundle_set.update(package.bundled_package_set)
        if ignore_assigned:
            non_assigned_set = copy(package_bundle_set)
            for package in package_bundle_set:
                if package.location.been_assigned:
                    non_assigned_set -= package.location.package_set
            package_bundle_set = non_assigned_set
        if all_location_packages:
            full_set = set()
            for package in package_bundle_set:
                full_set.update(package.location.package_set)
            package_bundle_set = full_set
        return package_bundle_set

    @staticmethod
    def get_delayed_packages(packages=all_packages, ignore_arrived=False) -> Set[Package]:
        delayed_packages = set()
        for package in packages:
            if (TimeConversion.get_datetime(package.hub_arrival_time) >
                    TimeConversion.get_datetime(config.DELIVERY_DISPATCH_TIME)):
                if ignore_arrived and package.status == DeliveryStatus.AT_HUB:
                    continue
                delayed_packages.add(package)
        return delayed_packages

    @staticmethod
    def get_deadline_packages(packages=all_packages, deadline_cutoff=config.DELIVERY_RETURN_TIME, ignore_routed=False):
        deadline_packages = set()
        for package in packages:
            if TimeConversion.get_datetime(package.deadline) < TimeConversion.get_datetime(deadline_cutoff):
                if not package.location.been_routed or ignore_routed:
                    deadline_packages.add(package)
        return deadline_packages

    @staticmethod
    def get_assigned_truck_packages(truck_id: int = None, packages=all_packages):
        truck_packages = set()
        for package in packages:
            if package.assigned_truck_id:
                if not truck_id or truck_id == package.assigned_truck_id:
                    truck_packages.add(package)
        return truck_packages

    @staticmethod
    def get_all_expected_status_update_times(special_times=None, start_time=config.PACKAGE_ARRIVAL_STATUS_UPDATE_TIME,
                                             end_time=config.DELIVERY_RETURN_TIME, in_locations=all_locations):
        status_updates_times = set()
        if special_times:
            status_updates_times = status_updates_times.union(special_times)
        start_date_time = TimeConversion.get_datetime(start_time)
        end_date_time = TimeConversion.get_datetime(end_time)
        for location in in_locations:
            if location.earliest_deadline:
                earliest_deadline = TimeConversion.get_datetime(location.earliest_deadline)
                if start_date_time <= earliest_deadline < end_date_time:
                    status_updates_times.add(earliest_deadline.time())
            if location.latest_package_arrival:
                latest_package_arrival_time = TimeConversion.get_datetime(location.latest_package_arrival)
                if start_date_time <= latest_package_arrival_time < end_date_time:
                    status_updates_times.add(latest_package_arrival_time.time())
        return status_updates_times

    @staticmethod
    def get_all_late_packages(current_time: time):
        late_packages = set()
        current_date_time = TimeConversion.get_datetime(current_time)
        for package in PackageHandler.all_packages:
            deadline_date_time = TimeConversion.get_datetime(package.deadline)
            if not package.location.been_routed and current_date_time >= deadline_date_time:
                late_packages.add(package)
        return late_packages

    @staticmethod
    def get_package_locations(in_packages: Set[Package], ignore_assigned=False) -> Set[Location]:
        locations = set()
        for package in in_packages:
            if not ignore_assigned or not package.location.been_assigned:
                locations.add(package.location)
        return locations

    @staticmethod
    def get_assigned_truck_id(in_location: Location):
        location_packages = PackageHandler.get_location_packages(in_location)
        truck_id = None
        for package in location_packages:
            if truck_id and truck_id != package.assigned_truck_id:
                return None
            if package.assigned_truck_id:
                truck_id = package.assigned_truck_id
        return truck_id

    @staticmethod
    def get_available_packages(current_time: time, in_packages=all_packages, ignore_assigned=False) -> Set[Package]:
        available_packages = set()
        for package in in_packages:
            if package.location.been_assigned and ignore_assigned:
                continue
            if TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time):
                available_packages.add(package)
        return available_packages

    @staticmethod
    def get_unconfirmed_packages(in_packages=all_packages):
        unconfirmed_packages = set()
        for package in in_packages:
            if not package.is_verified_address:
                unconfirmed_packages.add(package)
        return unconfirmed_packages
