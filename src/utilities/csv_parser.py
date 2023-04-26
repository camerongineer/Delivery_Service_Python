import csv
import re
from datetime import datetime

from src.config import DELIVERY_RETURN_TIME
from src.constants.delivery_status import DeliveryStatus
from src.constants.states import State
from src.constants.utah_cities import UtahCity
from src.models.location import Location
from src.models.package import Package


class CsvParser:
    @staticmethod
    def initialize_packages(file_name):
        packages = []
        with open(file_name, newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                package_id = int(row['Package ID'])
                address = row['Address']
                state = State['UTAH']
                city = UtahCity[row['City'].replace(" ", "_").upper()]
                zip_code = int(row['Zip'])
                is_verified_address = not row['Special Notes'].startswith('Wrong address')
                deadline = DELIVERY_RETURN_TIME if row['Delivery Deadline'] == 'EOD' else\
                    datetime.strptime(row['Delivery Deadline'], '%I:%M:%S %p').time()
                weight = int(row['Mass KILO'])
                status = DeliveryStatus['AT_HUB']
                special_note = row['Special Notes']
                packages.append(Package(package_id=package_id, address=address, city=city, state=state,
                                        zip_code=zip_code, is_verified_address=is_verified_address, deadline=deadline,
                                        weight=weight, status=status, special_note=special_note))

        return packages

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
