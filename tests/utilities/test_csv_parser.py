import os
from unittest import TestCase

from src.config import DISTANCE_CSV_FILE, PACKAGE_CSV_FILE
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location
from src.utilities.csv_parser import CsvParser


class TestCsvParser(TestCase):
    def setUp(self) -> None:
        self.packages = CsvParser.initialize_packages(PACKAGE_CSV_FILE)
        self.locations = CsvParser.initialize_locations(DISTANCE_CSV_FILE)

    def test_initialize_packages(self):
        for package in self.packages:
            assert package.package_id
            assert package.address
            assert package.city
            assert package.state
            assert package.zip_code
            assert package.deadline
            assert package.weight
            assert package.status == DeliveryStatus.AT_HUB

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
