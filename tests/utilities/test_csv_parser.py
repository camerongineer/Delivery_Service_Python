from datetime import time
from unittest import TestCase

from src.config import DISTANCE_CSV_FILE, PACKAGE_CSV_FILE
from src.constants.delivery_status import DeliveryStatus
from src.constants.states import State
from src.constants.utah_cities import UtahCity
from src.models.location import Location
from src.utilities.csv_parser import CsvParser


class TestCsvParser(TestCase):
    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations(DISTANCE_CSV_FILE)
        self.packages = CsvParser.initialize_packages(PACKAGE_CSV_FILE, self.locations)

    def test_initialize_packages(self):
        for package in self.packages:
            assert package.package_id and isinstance(package.package_id, int)
            assert package.location and isinstance(package.location, Location)
            assert package.location.city and isinstance(package.location.city, UtahCity)
            assert package.location.city.state and isinstance(package.location.city.state, State)
            assert package.deadline and isinstance(package.deadline, time)
            assert package.weight and isinstance(package.weight, int)
            assert package.status == DeliveryStatus.ON_ROUTE_TO_DEPOT

    def test_initialize_locations(self):
        hubs = 0
        for location in self.locations:
            if location.is_hub:
                hubs += 1
                assert hubs == 1
            assert location.name and isinstance(location.name, str)
            assert location.address and isinstance(location.address, str)
            assert location.zip_code and isinstance(location.zip_code, int)
            assert len(location.distance_dict.keys()) == len(self.locations) - 1
            for dist_location, distance in location.distance_dict.items():
                assert dist_location and isinstance(dist_location, Location)
                assert distance and isinstance(distance, float)

    def test_all_other_locations_in_location_dict(self):
        for location in self.locations:
            total_in_location_dict = 0
            for other_location in location.distance_dict.keys():
                if other_location in location.distance_dict.keys():
                    total_in_location_dict += 1
            assert total_in_location_dict == len(self.locations) - 1
