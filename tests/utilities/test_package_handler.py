from datetime import time
from unittest import TestCase

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.truck import Truck
from src.utilities.csv_parser import CsvParser
from src.utilities.custom_hash import CustomHash
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder


class TestPackageHandler(TestCase):
    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations()
        self.packages = CsvParser.initialize_packages(self.locations)
        self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
        self.custom_hash.add_all_packages(self.packages)
        self.truck_1 = Truck(1)
        self.truck_2 = Truck(2)
        self.truck_3 = Truck(3)

    def tearDown(self) -> None:
        pass

    def test_load_packages_at_hub(self):
        self.truck_1.location = None
        assert not PackageHandler.load_packages(config.STANDARD_PACKAGE_ARRIVAL_TIME, self.truck_1, [self.packages[0]])
        assert not len(self.truck_1)
        self.truck_1.location = Truck.hub_location
        assert PackageHandler.load_packages(config.STANDARD_PACKAGE_ARRIVAL_TIME, self.truck_1, [{self.packages[0]}])
        assert len(self.truck_1) == 1
        assert self.packages[0] in self.truck_1

    def test_load_packages_for_assigned_truck(self):
        required_truck_id = 2
        required_package_ids = [3, 18, 36, 38]
        truck_2_packages = RouteBuilder.get_assigned_truck_packages(self.packages, required_truck_id)
        PackageHandler.bulk_status_update(config.STANDARD_PACKAGE_ARRIVAL_TIME, self.packages, self.locations)
        assert list(truck_2_packages)[0].status is DeliveryStatus.AT_HUB
        assert not PackageHandler.load_packages(config.STANDARD_PACKAGE_ARRIVAL_TIME, self.truck_1, [truck_2_packages])
        assert not len(self.truck_1)
        assert list(truck_2_packages)[0].status is DeliveryStatus.AT_HUB
        assert PackageHandler.load_packages(config.STANDARD_PACKAGE_ARRIVAL_TIME, self.truck_2, [truck_2_packages])
        assert len(self.truck_2) == len(required_package_ids)
        for package in truck_2_packages:
            assert self.truck_2.get_package(package.package_id) is package
            assert package.status is DeliveryStatus.LOADED
            assert package.package_id in required_package_ids

    def test_update_delivery_location(self):
        assert not len(self.truck_1)
        self.truck_1.add_package(self.custom_hash.get_package(9))
        package_to_update = self.truck_1.get_package(9)
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

    def test_bulk_status_update(self):
        current_time = time(hour=7)

    def test_get_mileage(self):
        self.truck_1.dispatch_time = config.DELIVERY_DISPATCH_TIME
        self.truck_1.completion_time = time(hour=10, minute=37, second=5)
        self.truck_1.pause(time(hour=10, minute=30), time(hour=10, minute=33))
        current_time = time(hour=17, minute=31)
        print(self.truck_1.get_mileage(current_time))


    def test_get_current_location(self):
        self.truck_1.previous_location = self.locations[0]
        for package in self.packages:
            pass
