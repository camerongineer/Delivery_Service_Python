import csv
import re
from datetime import datetime, time
from typing import List

from src import config
from src.constants.utah_cities import UtahCity
from src.models.location import Location
from src.models.package import Package
from src.models.truck import Truck


__all__ = ['CsvParser']


def _set_arrival_time(package: Package):
    if package.special_note.startswith('Delayed'):
        match = re.search(r'(\d{1,2}):(\d{2})\s+(am|pm)', package.special_note)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            if match.group(3) == 'pm' and hour != 12:
                hour += 12
            elif match.group(3) == 'am' and hour == 12:
                hour = 0
            package.hub_arrival_time = time(hour=hour, minute=minute)
    else:
        package.hub_arrival_time = config.STANDARD_PACKAGE_ARRIVAL_TIME


def _set_assigned_truck(package: Package):
    if package.special_note.startswith('Can only be on truck '):
        pattern = r'\d+'
        match = re.findall(pattern, package.special_note).pop()
        package.assigned_truck_id = int(match)


def _set_earliest_location_deadline(location: Location, in_deadline_time: time):
    current_location_deadline = datetime.combine(datetime.min, location.earliest_deadline)
    in_deadline = datetime.combine(datetime.min, in_deadline_time)
    if in_deadline < current_location_deadline:
        location.earliest_deadline = in_deadline_time


class CsvParser:
    @staticmethod
    def initialize_locations(filepath=config.DISTANCE_CSV_FILE):
        locations = []
        with open(filepath) as csv_file:
            columns = csv.reader(csv_file).__next__()
            for column in columns[2:]:
                name, address, *overflow = column.split('\n')
                address = address.strip()[:-1] if not str(address[-1]).isalnum() else address.strip()
                location = Location(name.strip(), address)
                if overflow:
                    *city_state, zip_code = overflow[0].split()
                    location.set_zip_code(int(zip_code))
                locations.append(location)

            name_address_rows = []
            address_zip_rows = []
            distances_rows = []
            for csv_row in csv.reader(csv_file):
                name_address, address_zip, *distances = csv_row
                name_address_rows.append(name_address)
                address_zip_rows.append(address_zip)
                distances_rows.append(distances)

            for i, row in enumerate(distances_rows):
                name = str(name_address_rows[i].split('\n')[0]).strip()
                if str(address_zip_rows[i]).strip() == 'HUB':
                    locations[i].set_location_as_hub()
                    Truck.hub_location = locations[i]
                zip_match = re.search(r'\((\d+)\)', address_zip_rows[i])
                if zip_match:
                    zip_code = int(zip_match.group(1))
                    location = locations[i]
                    if not location.zip_code and name == location.name:
                        location.set_zip_code(zip_code)

                distance_dict = {}
                for j in range(0, i):
                    distance_dict[locations[j]] = float(distances_rows[i][j])
                for k in range(i + 1, len(distances_rows)):
                    distance_dict[locations[k]] = float(distances_rows[k][i])

                locations[i].set_distance_dict(distance_dict)
        return locations

    @staticmethod
    def initialize_packages(locations: List[Location], filepath=config.PACKAGE_CSV_FILE):
        packages = []
        with open(filepath, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                row: dict = row
                package_id = int(row['Package ID'])
                address: str = row['Address'].strip()
                city = UtahCity[row['City'].replace(' ', '_').upper()]
                zip_code = int(row['Zip'].strip())
                package_location = None
                for location in locations:
                    if location.address == address and location.zip_code == zip_code:
                        package_location = location
                        break
                if not package_location:
                    raise ImportError
                package_location.set_city(city)
                deadline = config.DELIVERY_RETURN_TIME if row['Delivery Deadline'] == 'EOD' else \
                    datetime.strptime(row['Delivery Deadline'], '%I:%M:%S %p').time()
                weight = int(row['Mass KILO'])
                special_note = row['Special Notes']
                is_verified_address = not special_note.startswith('Wrong address')
                package = Package(package_id=package_id, location=package_location,
                                  is_verified_address=is_verified_address, deadline=deadline,
                                  weight=weight, special_note=special_note)
                _set_arrival_time(package)
                _set_earliest_location_deadline(package.location, package.deadline)
                _set_assigned_truck(package)
                packages.append(package)
        return packages
