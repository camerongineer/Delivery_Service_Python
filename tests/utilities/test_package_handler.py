from datetime import time
from unittest import TestCase

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.exceptions import AddressUpdateException
from src.models.truck import Truck
from src.utilities.custom_hash import CustomHash
from src.utilities.package_handler import PackageHandler


class TestPackageHandler(TestCase):
    def setUp(self) -> None:
        self.locations = PackageHandler.all_locations
        self.packages = PackageHandler.all_packages
        self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
        self.custom_hash.add_all_packages(self.packages)
        self.truck_1 = Truck(1)
        self.truck_2 = Truck(2)
        self.truck_3 = Truck(3)

    def tearDown(self) -> None:
        pass

    def test_update_delivery_location(self):
        assert not len(self.truck_1)
        self.truck_1.add_package(self.custom_hash.get_package(9))
        package_to_update = self.truck_1.get_package(9)
        original_location = package_to_update.location
        update_time = time(10, 20)
        assert not package_to_update.is_verified_address
        assert package_to_update.location.address == '300 State St'
        assert package_to_update.location.zip_code == 84103
        assert original_location.package_total() == 3
        assert package_to_update in original_location
        assert not PackageHandler.update_delivery_location(
            locations_list=self.locations, package=package_to_update, updated_address='', current_time=update_time)
        assert not package_to_update.is_verified_address
        assert package_to_update.location.address == '300 State St'
        assert package_to_update.location.zip_code == 84103
        with self.assertRaises(AddressUpdateException):
            PackageHandler.update_delivery_location(
                locations_list=self.locations, package=package_to_update,
                updated_address='410 S State St., Salt Lake City, UT 84111', current_time=update_time)
        assert package_to_update.location.address == '410 S State St'
        assert package_to_update.location.zip_code == 84111
        assert package_to_update.is_verified_address
        assert original_location.package_total() == 2
        new_location = package_to_update.location
        assert new_location.package_total() == 4
        assert package_to_update in new_location
        assert package_to_update not in original_location

    def test_get_bundled_packages(self):
        bundled_packages = PackageHandler.get_bundled_packages(all_location_packages=False)
        bundled_package_ids = [13, 14, 15, 16, 19, 20]
        assert len(bundled_packages) == len(bundled_package_ids)
        for package in bundled_packages:
            assert package.package_id in bundled_package_ids

    def test_get_all_packages_at_bundled_locations(self):
        all_packages_at_bundle_locations = PackageHandler.get_bundled_packages(all_location_packages=True)
        required_bundled_package_ids = [13, 14, 15, 16, 19, 20, 21, 34, 39]
        assert len(all_packages_at_bundle_locations) == len(required_bundled_package_ids)
        for package_id in required_bundled_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_bundle_locations

    def test_ignore_assigned_at_bundled_locations(self):
        bundled_packages = PackageHandler.get_bundled_packages(ignore_assigned=True)
        bundled_package_ids = [13, 14, 15, 16, 19, 20]
        assert len(bundled_packages) == len(bundled_package_ids)
        location_to_assign = self.custom_hash.get_package(20).location
        location_to_assign.been_assigned = True
        bundled_packages = PackageHandler.get_bundled_packages(ignore_assigned=True)
        bundled_package_ids = [13, 14, 15, 16, 19]
        assert len(bundled_packages) == len(bundled_package_ids)
        all_bundled_packages = PackageHandler.get_bundled_packages(all_location_packages=True, ignore_assigned=True)
        all_bundled_package_ids = [13, 14, 15, 16, 19, 34, 39]
        assert len(all_bundled_packages) == len(all_bundled_package_ids)
        for package in all_bundled_packages:
            assert not package.location.been_assigned
            assert package.package_id in all_bundled_package_ids

    def test_get_assigned_truck_packages(self):
        required_truck_id = 2
        required_package_ids = [3, 18, 36, 38]
        truck_packages = PackageHandler.get_assigned_truck_packages(required_truck_id)
        assert len(truck_packages) == len(required_package_ids)
        for package_id in required_package_ids:
            assert self.custom_hash.get_package(package_id) in truck_packages
        for package in self.packages:
            if str(package.special_note).startswith('Can only be on truck '):
                assert package.package_id in required_package_ids
                assert package.assigned_truck_id == required_truck_id
            else:
                assert package.package_id not in required_package_ids
                assert not package.assigned_truck_id

    def test_get_delayed_packages(self):
        PackageHandler.bulk_status_update(config.STANDARD_PACKAGE_ARRIVAL_TIME)
        delayed_packages = PackageHandler.get_delayed_packages(self.packages)
        delayed_package_ids = [6, 25, 28, 32]
        assert len(delayed_packages) == len(delayed_package_ids)
        for package in self.packages:
            if package not in delayed_packages:
                assert not str(package.special_note).startswith('Delayed')
                assert package.hub_arrival_time is config.STANDARD_PACKAGE_ARRIVAL_TIME
        for package_id in delayed_package_ids:
            assert self.custom_hash.get_package(package_id).hub_arrival_time == time(hour=9, minute=5)
        arrived_package = self.custom_hash.get_package(6)
        arrived_package.status = DeliveryStatus.AT_HUB
        delayed_packages = PackageHandler.get_delayed_packages(self.packages, ignore_arrived=True)
        assert len(delayed_packages) == len(delayed_package_ids) - 1

    def test_get_available_packages(self):
        available_packages = PackageHandler.get_available_packages(current_time=time(8))
        delayed_package_ids = [6, 25, 28, 32]
        assert len(PackageHandler.all_packages) == len(available_packages) + len(delayed_package_ids)
        for package in available_packages:
            assert package.package_id not in delayed_package_ids
        assigned_location = list(self.packages)[0].location
        assigned_location.been_assigned = True
        available_packages = PackageHandler.get_available_packages(current_time=time(8), ignore_assigned=True)
        for package in available_packages:
            assert package.location is not assigned_location
