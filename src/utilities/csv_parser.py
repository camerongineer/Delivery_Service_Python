import csv
import re
from datetime import datetime, time
from typing import List

from src import config
from src.constants import UtahCity, DeliveryStatus
from src.models import Location, Package

__all__ = ['CsvParser']


class CsvParser:
    @staticmethod
    def initialize_locations(filename):
        locations = []
        with open(filename) as csv_file:
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
    def initialize_packages(file_name: str, locations: List[Location]):
        packages = []
        with open(file_name, newline='') as csv_file:
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
                if special_note.startswith('Delayed'):
                    status = DeliveryStatus.ON_ROUTE_TO_DEPOT
                else:
                    status = DeliveryStatus.AT_HUB
                package = Package(package_id=package_id, location=package_location,
                                  is_verified_address=is_verified_address, deadline=deadline,
                                  weight=weight, status=status, special_note=special_note)
                _set_arrival_time(package)
                packages.append(package)
        return packages


def _set_arrival_time(package: Package):
    if str(package.special_note).startswith('Delayed'):
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
