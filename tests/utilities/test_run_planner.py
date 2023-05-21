from copy import copy
from datetime import time
from unittest import TestCase
from unittest.mock import patch

from src import config
from src.models.route_run import RouteRun
from src.models.truck import Truck
from src.utilities.package_handler import PackageHandler
from src.utilities.run_planner import RunPlanner


def _set_all_locations_assigned(packages):
    for package in packages:
        package.location.been_assigned = True


def _get_packages_by_id(list_of_ids):
    package_set = set()
    for package_id in list_of_ids:
        package_set.add(PackageHandler.package_hash.get_package(package_id))
    return package_set


class TestRunPlanner(TestCase):

    def setUp(self) -> None:
        self.locations = PackageHandler.all_locations
        self.packages = PackageHandler.all_packages
        self.package_hash = PackageHandler.package_hash

    def test_early_return_run_build(self):
        early_return_packages = PackageHandler.get_bundled_packages()
        package_locations = PackageHandler.get_package_locations(early_return_packages)
        target_package = self.package_hash.get_package(15)
        target_location = target_package.location
        early_return_run = RunPlanner.build(target_location, return_to_hub=True, focused_run=True, assigned_truck_id=1)

        assert len(early_return_run.ordered_route) == 4
        assert target_location in early_return_run.ordered_route
        assert sum([location.package_total() for location in early_return_run.ordered_route]) == 4
        assert len(early_return_run.required_packages) == 7
        for location in early_return_run.locations:
            assert location in package_locations
        assert all(package in early_return_run.required_packages for package in early_return_packages)
        assert not all(package in early_return_packages for package in early_return_run.required_packages)
        required_package_copy = copy(early_return_run.required_packages)
        for package in required_package_copy:
            if package.location.been_assigned:
                early_return_run.required_packages.remove(package)
        assert len(early_return_run.required_packages) == 3
        early_return_run = RunPlanner.build(target_location, return_to_hub=True, focused_run=True)
        assert target_location.been_assigned
        assert not early_return_run

    def test_furthest_from_hub_location_run_build(self):
        truck1 = Truck(1)
        truck = Truck(2)
        run = RunPlanner.build(self.package_hash.get_package(15).location, truck1)
        focused_run = RunPlanner.build(self.package_hash.get_package(3).location, truck, start_time=time(9, 5), has_assigned_truck_focus=True)

        furthest_location_run = RunPlanner.build(self.package_hash.get_package(22).location, truck, start_time=time(9, 5))
        package_count = 0
        estimate_mileage = 0
        min_miles = 100
        min_package = -1
        for i in range(1, 41):
            print(i)
            furthest_location_run = RunPlanner.build(self.package_hash.get_package(i).location, truck, start_time=time(9, 5))
            if furthest_location_run.estimated_mileage < min_miles and furthest_location_run.package_total() > 10:
                min_miles = furthest_location_run.estimated_mileage
                min_package = i
            for package in PackageHandler.all_packages:
                package.location.been_assigned = False
        print(min_miles)
        print(min_package)
        # package_count += furthest_location_run.package_total()
        # estimate_mileage += furthest_location_run.estimated_mileage
        # package_ids = [11, 18, 32, 31, 24, 23, 25, 26, 36, 6, 17]
        # furthest_packages = _get_packages_by_id(package_ids)
        # furthest_locations = PackageHandler.get_package_locations(furthest_packages)
        # furthest_location = self.package_hash.get_package(11).location
        # print(furthest_location_run.get_estimated_mileage_at_location(furthest_location))
        # print(furthest_location_run.get_estimated_time_at_location(furthest_location))
        # furthest_location_run = RunPlanner.build(furthest_location, return_to_hub=True, focused_run=True)
        # package_count += furthest_location_run.package_total()
        # estimate_mileage += furthest_location_run.estimated_mileage
        # furthest_location = self.package_hash.get_package(3).location
        # furthest_location_run = RunPlanner.build(furthest_location, return_to_hub=False, focused_run=False,
        #                                          ignore_delayed_locations=True, start_time=time(9, 21), assigned_truck_id=2)
        # package_count += furthest_location_run.package_total()
        # estimate_mileage += furthest_location_run.estimated_mileage
        # furthest_location = self.package_hash.get_package(22).location
        # furthest_location_run = RunPlanner.build(furthest_location, return_to_hub=True, focused_run=False,
        #                                          ignore_delayed_locations=True, start_time=time(9, 5), assigned_truck_id=2)
        # package_count += furthest_location_run.package_total()
        # estimate_mileage += furthest_location_run.estimated_mileage
        for location in furthest_location_run.ordered_route:
            print(location)
        for package in furthest_location_run.required_packages:
            print(package)
        print(furthest_location_run.delayed_location_total())
        print(furthest_location_run.assigned_truck_location_total())
        print(furthest_location_run.unconfirmed_location_total())
        print(furthest_location_run.bundled_location_total())
        print(furthest_location_run.early_deadline_total())
        print(furthest_location_run.estimated_mileage)
        print(furthest_location_run.package_total())
        print(furthest_location_run.estimated_completion_time)

        print(package_count)
        print(estimate_mileage)
        print(PackageHandler.get_available_packages(current_time=time(10), ignore_assigned=True))
        print(len(PackageHandler.get_available_packages(current_time=time(10), ignore_assigned=True)))
