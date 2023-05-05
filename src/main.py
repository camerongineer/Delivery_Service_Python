from datetime import datetime, timedelta, date

from src import *
from src.constants.delivery_status import DeliveryStatus
from src.utilities.route_builder import RouteBuilder

all_locations = CsvParser.initialize_locations(DISTANCE_CSV_FILE)
all_packages = CsvParser.initialize_packages(PACKAGE_CSV_FILE, all_locations)

truck_1 = CustomHash(NUM_TRUCK_CAPACITY)

sum_of_all_distances = 0.0
min_sum_of_distances = 1000.0
min_location = None
max_sum_of_distances = 0.0
max_location = None

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
current_time = DELIVERY_DISPATCH_TIME
total_miles = 0.0

hub = all_locations[0]

all_packages.sort(key=lambda p: p.location.distance_dict[hub])

for list_package in all_packages:
    package = truck_1.get_package(list_package.package_id)

    if not truck_1.get_package(list_package.package_id).is_verified_address or package.status == DeliveryStatus.DELIVERED:
        continue

    last_location = current_location
    current_location = package.location
    if last_location is current_location:
        miles_from_last_stop = 0
        time_passed_since_last_stop = 0
    else:
        miles_from_last_stop = current_location.distance_dict[last_location]
        time_passed_since_last_stop = last_location.distance_dict[current_location] / DELIVERY_TRUCK_MPH
    total_miles += miles_from_last_stop
    time_in_seconds = int(time_passed_since_last_stop * 3600)
    delta = timedelta(seconds=time_in_seconds)

    current_time = (datetime.combine(date.today(), current_time) + delta).time()
    print(f'{last_location.name} to {current_location.name} -> {miles_from_last_stop:.1f} miles, elapsed time: {int(time_passed_since_last_stop * 60)} min')

    print(current_time, f'{total_miles:.1f}', 'miles', '::: ', list_package.package_id)
