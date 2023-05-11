from datetime import time, datetime
from typing import List, Set



__all__ = ['PackageHandler']

from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck
from src.utilities.time_conversion import TimeConversion


def _is_loadable_package_set(truck: Truck, in_package_set: Set[Package]) -> bool:
    for in_package in in_package_set:
        if in_package.status is not DeliveryStatus.AT_HUB:
            return False
        if in_package.assigned_truck_id and in_package.assigned_truck_id != truck.truck_id:
            return False
    return True


class PackageHandler:
    @staticmethod
    def load_packages(current_time: time, truck: Truck, package_sets: List[Set[Package]]):
        for package_set in package_sets:
            if truck.previous_location is not Truck.hub_location or not _is_loadable_package_set(truck, package_set):
                return False
        for package_set in package_sets:
            for package in package_set:
                package.update_status(DeliveryStatus.LOADED, current_time)
                truck.add_package(package)
            return True

    @staticmethod
    def update_delivery_location(locations_list: List[Location], package: Package, updated_address: str):
        try:
            address, city, state_zip = updated_address.split(', ')
            zip_code = int(state_zip.split(' ')[1])
            for location in locations_list:
                if str(address).startswith(location.address) and location.zip_code == zip_code:
                    package.location = location
                    package.is_verified_address = True
                    return True
        except (ValueError, TypeError):
            return False
        return False

    @staticmethod
    def bulk_status_update(current_time: time, updated_status: DeliveryStatus, packages: List[Package]):
        for package in packages:
            if package.status is DeliveryStatus.ON_ROUTE_TO_DEPOT and\
                    TimeConversion.is_time_at_or_before_other_time(package.hub_arrival_time, current_time):
                print(f'Package: {package.package_id:02} status changed from "{package.status.description}" to "{updated_status.description}"')
                package.update_status(updated_status, current_time)

    @staticmethod
    def delayed_packages_arrived(in_packages: List[Package], current_time: time):
        latest_arrival = in_packages[0].location.latest_package_arrival
        if TimeConversion.is_time_at_or_before_other_time(latest_arrival, current_time):
            for in_package in in_packages:
                in_package.status = DeliveryStatus.AT_HUB
