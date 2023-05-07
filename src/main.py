from datetime import datetime, timedelta, date
from typing import List

from src import config
from src.constants import DeliveryStatus
from src.models import Truck, Location, Package
from src.utilities import CsvParser, RouteBuilder


def nearest_neighbors(in_location: Location, in_packages: List[Package]):
    sorted_location_dict = sorted(in_location.distance_dict.items(), key=lambda _location: _location[1])
    for location, distance in sorted_location_dict:
        if not location.been_visited:
            if is_location_in_package_set(location, in_packages):
                out_packages = RouteBuilder.get_location_packages(location, in_packages)
            else:
                out_packages = RouteBuilder.get_location_packages(location, all_packages)
            # if not is_deliverable_package_set(list(out_packages)):
            #     out_packages.pop().location.been_visited = True
            #     continue
            return out_packages
    return None


def is_location_in_package_set(in_location: Location, in_packages: List[Package]) -> bool:
    for in_package in in_packages:
        if in_package.location == in_location:
            return True
    return False


def is_deliverable_package_set(in_packages: List[Package]):
    for in_package in in_packages:
        if not in_package.is_verified_address or in_package.status == DeliveryStatus.ON_ROUTE_TO_DEPOT:
            return False
    return True


all_locations = CsvParser.initialize_locations(config.DISTANCE_CSV_FILE)
all_packages = CsvParser.initialize_packages(config.PACKAGE_CSV_FILE, all_locations)

truck_1 = Truck()
truck_2 = Truck()
truck_3 = Truck()

sum_of_all_distances = 0.0
min_sum_of_distances = 1000.0
min_location = None
max_sum_of_distances = 0.0
max_location = None

packages = list(
    RouteBuilder.get_all_packages_at_bundled_locations(list(RouteBuilder.get_bundled_packages(all_packages).pop()),
                                                       all_packages))

for package in all_packages:
    sum_of_distances = sum(package.location.distance_dict.values())
    sum_of_all_distances += sum_of_distances
    if sum_of_distances > max_sum_of_distances:
        max_sum_of_distances = sum_of_distances
        max_location = package.location
    if sum_of_distances < min_sum_of_distances:
        min_sum_of_distances = sum_of_distances
        min_location = package.location
    truck_1.add_package(package)

print(sum_of_all_distances / len(all_locations) / len(all_packages))

current_location = [location for location in all_locations if location.is_hub][0]
current_time = config.DELIVERY_DISPATCH_TIME
total_miles = 0.0

hub = all_locations[0]
next_packages = nearest_neighbors(hub, packages)
hub.been_visited = True
last_location = None

all_packages.sort(key=lambda _package: _package.location.distance_dict[hub])
packages_delivered = 0

while next_packages: #and packages_delivered < 17:
    amount_dropped = 0
    if last_location and current_location and last_location is not hub and current_location is not hub:
        last_to_hub_to_current = last_location.distance_dict[hub] + current_location.distance_dict[hub]
        print(f"\n\nExtra miles if return to hub = {last_to_hub_to_current - last_location.distance_dict[current_location]:.1f}\n\n")
    last_location = current_location
    current_location = list(next_packages)[0].location
    miles_from_last_stop = current_location.distance_dict[last_location]
    time_passed_since_last_stop = last_location.distance_dict[current_location] / config.DELIVERY_TRUCK_MPH
    total_miles += miles_from_last_stop

    time_in_seconds = int(time_passed_since_last_stop * 3600)
    delta = timedelta(seconds=time_in_seconds)
    current_time = (datetime.combine(date.today(), current_time) + delta).time()
    print(
        f'Current Time:{current_time} | Total Miles: {total_miles:.1f} | {last_location.name} to {current_location.name} -> {miles_from_last_stop:.1f} miles, elapsed time: {int(time_passed_since_last_stop * 60)} min')
    miles_from_last_stop = current_location.distance_dict[last_location]
    print(f'{len(next_packages)} packages at this location | {current_location.name}: ')
    for list_package in list(next_packages):
        package = truck_1.get_package(list_package.package_id)

        amount_dropped += 1
        print(f'Package ID:{package.package_id} was delivered at {current_location.address} | Total Delivered: {amount_dropped + packages_delivered} | {current_location.distance_dict[hub]:.1f} miles from hub')
        # if amount_dropped + packages_delivered >= 16:
        #     break
    packages_delivered += amount_dropped
    current_location.been_visited = True
    next_packages = nearest_neighbors(current_location, packages)
