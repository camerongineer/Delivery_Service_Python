from unittest import TestCase

from src.config import PACKAGE_CSV_FILE, DISTANCE_CSV_FILE, NUM_TRUCK_CAPACITY
from src.models.package import Package
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash


class TestCustomHash(TestCase):

    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations(DISTANCE_CSV_FILE)
        self.packages = CsvParser.initialize_packages(PACKAGE_CSV_FILE, self.locations)
        self.custom_hash = CustomHash(NUM_TRUCK_CAPACITY)

    def test_add_package(self):
        for i in range(1, 41):
            self.custom_hash = CustomHash(i)
            for j in range(len(self.packages)):
                package_id = j + 1
                assert not self.custom_hash.get_package(package_id)
                assert self.custom_hash.add_package(package=self.packages[j])
                assert not self.custom_hash.add_package(package=self.packages[j])
            assert len(self.packages) == len(self.custom_hash)

    def test_get_package(self):
        for package in self.packages:
            self.custom_hash.add_package(package)
        for i in range(len(self.packages)):
            package = self.packages[i]
            hash_package = self.custom_hash.get_package(package.package_id)
            assert isinstance(package, Package)
            assert package is hash_package

    def test_remove_package(self):
        for i in range(1, 41):
            self.custom_hash = CustomHash(i)
            for j in range(len(self.packages) - 1, 0, -1):
                package_id = j + 1
                assert not self.custom_hash.remove_package(package_id)
                self.custom_hash.add_package(package=self.packages[j])
                assert self.custom_hash.remove_package(package_id)
            assert len(self.custom_hash) == 0

