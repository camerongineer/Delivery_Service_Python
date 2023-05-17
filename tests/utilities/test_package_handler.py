from datetime import time
from unittest import TestCase

from src import config
from src.constants.delivery_status import DeliveryStatus
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

    def test_load_packages_at_hub(self):
        self.truck_1.current_location = None
        self.truck_1.set_clock(config.STANDARD_PACKAGE_ARRIVAL_TIME)
        assert not PackageHandler.load_packages(self.truck_1, [self.packages[0]])
        assert not len(self.truck_1)
        self.truck_1.current_location = Truck.hub_location
        assert self.packages[0].status == DeliveryStatus.AT_HUB
        assert PackageHandler.load_packages(self.truck_1, [{self.packages[0]}])
        assert len(self.truck_1) == 1
        assert self.packages[0] in self.truck_1
        assert self.packages[0] is self.truck_1.get_package(self.packages[0].package_id)
        assert self.packages[0].status == DeliveryStatus.LOADED
        assert self.packages[0].status_update_dict[self.truck_1.clock] == DeliveryStatus.LOADED

    def test_load_packages_for_assigned_truck(self):
        self.truck_1.set_clock(config.STANDARD_PACKAGE_ARRIVAL_TIME)
        self.truck_2.set_clock(config.STANDARD_PACKAGE_ARRIVAL_TIME)
        required_truck_id = 2
        required_package_ids = [3, 18, 36, 38]
        truck_2_packages = PackageHandler.get_assigned_truck_packages(required_truck_id)
        PackageHandler.bulk_status_update(config.STANDARD_PACKAGE_ARRIVAL_TIME)
        assert list(truck_2_packages)[0].status is DeliveryStatus.AT_HUB
        assert not PackageHandler.load_packages(self.truck_1, [truck_2_packages])
        assert not len(self.truck_1)
        assert list(truck_2_packages)[0].status is DeliveryStatus.AT_HUB
        assert PackageHandler.load_packages(self.truck_2, [truck_2_packages])
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
        assert len(PackageHandler.get_location_package_dict(self.packages)[original_location]) == 3
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
        assert len(PackageHandler.get_location_package_dict(self.packages)[original_location]) == 2
        new_location = package_to_update.location
        assert len(PackageHandler.get_location_package_dict(self.packages)[new_location]) == 4

    # def test_bulk_status_update(self):
    #     current_time = time(hour=7)

    # def test_get_mileage(self):
    #     self.truck_1.dispatch_time = config.DELIVERY_DISPATCH_TIME
    #     self.truck_1.completion_time = time(hour=10, minute=37, second=5)
    #     self.truck_1.pause(time(hour=10, minute=30), time(hour=10, minute=33))
    #     current_time = time(hour=17, minute=31)
    #     print(self.truck_1.get_mileage(current_time))

    def test_get_location_packages(self):
        sole_package_at_location = self.custom_hash.get_package(22)
        one_package = PackageHandler.get_location_packages(sole_package_at_location.location)
        assert len(one_package) == 1
        assert one_package.pop() is sole_package_at_location
        one_package_of_many_at_location = self.custom_hash.get_package(8)
        many_packages = PackageHandler.get_location_packages(one_package_of_many_at_location.location)
        assert len(many_packages) == 3
        assert one_package_of_many_at_location in many_packages
        for package in many_packages:
            if one_package_of_many_at_location.package_id == package.package_id:
                assert one_package_of_many_at_location is package
            else:
                assert one_package_of_many_at_location is not package

    def test_get_location_package_dict(self):
        location_package_dict = PackageHandler.get_location_package_dict()
        assert len(location_package_dict.keys()) == len(self.locations) - 1
        assert sum(len(package_list) for package_list in location_package_dict.values()) == len(self.packages)

    def test_get_bundled_packages(self):
        bundled_packages = PackageHandler.get_bundled_packages()
        bundled_package_ids = [13, 14, 15, 16, 19, 20]
        assert len(bundled_packages) == len(bundled_package_ids)
        for package in bundled_packages:
            assert package.package_id in bundled_package_ids

    def test_get_all_packages_at_bundled_locations(self):
        bundled_packages = PackageHandler.get_bundled_packages()
        all_packages_at_bundle_locations =\
            PackageHandler.get_all_packages_at_bundled_locations(list(bundled_packages))
        required_bundled_package_ids = [13, 14, 15, 16, 19, 20, 21, 34, 39]
        assert len(all_packages_at_bundle_locations) == len(required_bundled_package_ids)
        for package_id in required_bundled_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_bundle_locations

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

    def test_get_all_packages_at_assigned_truck_locations(self):
        assigned_truck_bundle = PackageHandler.get_assigned_truck_packages(truck_id=2)
        all_packages_at_location_assigned_to_truck =\
            PackageHandler.get_all_packages_at_bundled_locations(assigned_truck_bundle, self.packages)
        required_assigned_truck_package_ids = [3, 5, 18, 36, 37, 38]
        assert len(all_packages_at_location_assigned_to_truck) == len(required_assigned_truck_package_ids)
        for package_id in required_assigned_truck_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_location_assigned_to_truck

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

    def test_get_deadline_packages(self):
        deadline_packages = PackageHandler.get_deadline_packages(self.packages)
        deadline_package_ids = [1, 6, 13, 14, 15, 16, 20, 25, 29, 30, 31, 34, 37, 40]
        assert len(deadline_packages) == len(deadline_package_ids)
        for package in self.packages:
            if package not in deadline_packages:
                assert package.deadline == config.DELIVERY_RETURN_TIME
            else:
                assert package.deadline != config.DELIVERY_RETURN_TIME
        for package_id in deadline_package_ids:
            if package_id == 15:
                assert self.custom_hash.get_package(package_id).deadline == time(hour=9, minute=0)
            else:
                assert self.custom_hash.get_package(package_id).deadline == time(hour=10, minute=30)
        deadline_packages = PackageHandler.get_deadline_packages(self.packages, time(hour=10, minute=31))
        assert len(deadline_packages) == len(deadline_package_ids)
        deadline_packages = PackageHandler.get_deadline_packages(self.packages, time(hour=10, minute=30))
        assert len(deadline_packages) == 1
        deadline_packages = PackageHandler.get_deadline_packages(self.packages, time(hour=9, minute=1))
        nine_am_deadline_package = deadline_packages.pop()
        assert nine_am_deadline_package.package_id == 15
        assert not deadline_packages
        nine_am_deadline_package.location.been_routed = True
        assert not PackageHandler.get_deadline_packages(self.packages, time(hour=9, minute=1))
        assert PackageHandler.get_deadline_packages(self.packages, time(hour=9, minute=1), ignore_routed=True)

    def test_get_all_packages_at_delayed_package_locations(self):
        delayed_truck_packages = PackageHandler.get_delayed_packages()
        all_packages_at_delayed_package_locations =\
            PackageHandler.get_all_packages_at_bundled_locations(list(delayed_truck_packages))
        required_delayed_location_package_ids = [6, 25, 26, 28, 31, 32]
        assert len(all_packages_at_delayed_package_locations) == len(required_delayed_location_package_ids)
        for package_id in required_delayed_location_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_delayed_package_locations

    def test_get_current_location(self):
        self.truck_1.previous_location = self.locations[0]
        for package in self.packages:
            pass

    def test_subtract_package_set(self):
        pass
