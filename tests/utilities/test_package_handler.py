from unittest import TestCase

from src import config
from src.utilities import CsvParser, RouteBuilder, PackageHandler


class TestPackageHandler(TestCase):
    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations(config.DISTANCE_CSV_FILE)
        self.packages = CsvParser.initialize_packages(config.PACKAGE_CSV_FILE, self.locations)
        self.custom_hash = PackageHandler.load_packages(self.packages)

    def test_update_delivery_location(self):
        package_to_update = self.custom_hash.get_package(9)
        original_location = package_to_update.location
        assert not package_to_update.is_verified_address
        assert package_to_update.location.address == '300 State St'
        assert package_to_update.location.zip_code == 84103
        assert len(RouteBuilder.get_location_package_dict(self.packages)[original_location]) == 3
        assert not PackageHandler.update_delivery_location(
            locations_list=self.locations, package=package_to_update, updated_address='')
        assert not package_to_update.is_verified_address
        assert package_to_update.location.address == '300 State St'
        assert package_to_update.location.zip_code == 84103
        assert PackageHandler.update_delivery_location(
            locations_list=self.locations, package=package_to_update,
            updated_address='410 S State St., Salt Lake City, UT 84111')
        assert package_to_update.location.address == '410 S State St'
        assert package_to_update.location.zip_code == 84111
        assert package_to_update.is_verified_address
        assert len(RouteBuilder.get_location_package_dict(self.packages)[original_location]) == 2
        new_location = package_to_update.location
        assert len(RouteBuilder.get_location_package_dict(self.packages)[new_location]) == 4
