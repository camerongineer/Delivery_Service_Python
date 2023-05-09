from unittest import TestCase

from src import config
from src.models import Package
from src.utilities import CsvParser, CustomHash


class TestCustomHash(TestCase):

    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations()
        self.packages = CsvParser.initialize_packages(self.locations)
        self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)

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

    def test_add_all_package(self):
        self.custom_hash.add_all_packages(self.packages)
        assert len(self.packages) == len(self.custom_hash)
        for package in self.packages:
            assert self.custom_hash.get_package(package.package_id) is package
