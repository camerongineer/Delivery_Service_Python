from datetime import time
from unittest import TestCase

from src import config
from src.models.truck import Truck
from src.utilities.route_builder import RouteBuilder


class TestRouteBuilder(TestCase):

    # def setUp(self) -> None:
    #     self.locations = CsvParser.initialize_locations()
    #     self.packages = CsvParser.initialize_packages(self.locations)
    #     self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
    #     for package in self.packages:
    #         self.custom_hash.add_package(package)

    def test_get_optimized_route(self):
        truck = Truck(2)
        manifest = RouteBuilder.get_optimized_route(truck)
        truck.dispatch_time = config.DELIVERY_DISPATCH_TIME
        # truck.pause(time(hour=9), time(hour=9, minute=30))
        current_time = time(hour=10)
        print(truck._travel_ledger)
        print(truck.get_mileage(current_time))
        print(truck.get_current_location(current_time))

    def test_get_location_packages(self):
        sole_package_at_location = self.custom_hash.get_package(22)
        one_package = RouteBuilder.get_location_packages(sole_package_at_location.location, self.packages)
        assert len(one_package) == 1
        assert one_package.pop() is sole_package_at_location
        one_package_of_many_at_location = self.custom_hash.get_package(8)
        many_packages = RouteBuilder.get_location_packages(one_package_of_many_at_location.location, self.packages)
        assert len(many_packages) == 3
        assert one_package_of_many_at_location in many_packages
        for package in many_packages:
            if one_package_of_many_at_location.package_id == package.package_id:
                assert one_package_of_many_at_location is package
            else:
                assert one_package_of_many_at_location is not package

    def test_get_location_package_dict(self):
        location_package_dict = RouteBuilder.get_location_package_dict(self.packages)
        assert len(location_package_dict.keys()) == len(self.locations) - 1
        assert sum(len(package_list) for package_list in location_package_dict.values()) == len(self.packages)

    def test_get_bundled_packages(self):
        package_bundles = RouteBuilder.get_bundled_packages(self.packages)
        assert len(package_bundles) == 1
        bundle = package_bundles.pop()
        assert not package_bundles
        bundled_package_ids = [13, 14, 15, 16, 19, 20]
        assert len(bundle) == len(bundled_package_ids)
        for package in bundle:
            assert package.package_id in bundled_package_ids

    def test_get_all_packages_at_bundled_locations(self):
        package_bundle = RouteBuilder.get_bundled_packages(self.packages).pop()
        all_packages_at_bundle_locations =\
            RouteBuilder.get_all_packages_at_bundled_locations(list(package_bundle), self.packages)
        required_bundled_package_ids = [13, 14, 15, 16, 19, 20, 21, 34, 39]
        assert len(all_packages_at_bundle_locations) == len(required_bundled_package_ids)
        for package_id in required_bundled_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_bundle_locations

    def test_get_assigned_truck_packages(self):
        required_truck_id = 2
        required_package_ids = [3, 18, 36, 38]
        truck_packages = RouteBuilder.get_assigned_truck_packages(self.packages, required_truck_id)
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
        assigned_truck_bundle = RouteBuilder.get_assigned_truck_packages(self.packages, truck_id=2)
        all_packages_at_location_assigned_to_truck =\
            RouteBuilder.get_all_packages_at_bundled_locations(assigned_truck_bundle, self.packages)
        required_assigned_truck_package_ids = [3, 5, 18, 36, 37, 38]
        assert len(all_packages_at_location_assigned_to_truck) == len(required_assigned_truck_package_ids)
        for package_id in required_assigned_truck_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_location_assigned_to_truck

    def test_get_delayed_packages(self):
        delayed_packages = RouteBuilder.get_delayed_packages(self.packages)
        delayed_package_ids = [6, 25, 28, 32]
        assert len(delayed_packages) == len(delayed_package_ids)
        for package in self.packages:
            if package not in delayed_packages:
                assert not str(package.special_note).startswith('Delayed')
                assert package.hub_arrival_time is config.STANDARD_PACKAGE_ARRIVAL_TIME
        for package_id in delayed_package_ids:
            assert self.custom_hash.get_package(package_id).hub_arrival_time == time(hour=9, minute=5)

    def test_get_all_packages_at_delayed_package_locations(self):
        delayed_truck_packages = RouteBuilder.get_delayed_packages(self.packages)
        all_packages_at_delayed_package_locations =\
            RouteBuilder.get_all_packages_at_bundled_locations(list(delayed_truck_packages), self.packages)
        required_delayed_location_package_ids = [6, 25, 26, 28, 31, 32]
        assert len(all_packages_at_delayed_package_locations) == len(required_delayed_location_package_ids)
        for package_id in required_delayed_location_package_ids:
            assert self.custom_hash.get_package(package_id) in all_packages_at_delayed_package_locations
