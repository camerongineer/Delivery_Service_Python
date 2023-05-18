from copy import copy
from unittest import TestCase

from src import config
from src.models.route_run import RouteRun
from src.utilities.package_handler import PackageHandler
from src.utilities.run_planner import RunPlanner


def _set_all_locations_assigned(packages):
    for package in packages:
        package.location.been_assigned = True


def _get_packages_by_id(list_of_ids):
    package_set = set()
    for id in list_of_ids:
        package_set.add(PackageHandler.package_hash.get_package(id))
    return package_set


class TestRunPlanner(TestCase):
    def setUp(self) -> None:
        self.locations = PackageHandler.all_locations
        self.packages = PackageHandler.all_packages
        self.package_hash = PackageHandler.package_hash
        self.early_run_packages = set()
        self.early_run_packages.add(self.package_hash.get_package(15))
        self.early_run_packages.add(self.package_hash.get_package(16))
        self.early_run_packages.add(self.package_hash.get_package(14))
        self.early_run_packages.add(self.package_hash.get_package(34))
        self.early_run_locations = PackageHandler.get_package_locations(self.early_run_packages)

    def test_early_return_run_build(self):
        early_return_packages = PackageHandler.get_bundled_packages()
        package_locations = PackageHandler.get_package_locations(early_return_packages)
        target_package = self.package_hash.get_package(15)
        target_location = target_package.location
        early_return_run = RunPlanner.build(target_location, return_to_hub=True, focused_run=True)

        assert len(early_return_run.ordered_route) == 4
        assert target_location in early_return_run.ordered_route
        assert sum([location.package_total() for location in early_return_run.ordered_route]) == 4
        assert len(early_return_run.required_packages) == 9
        assert all(package in early_return_run.required_packages for package in early_return_packages)
        assert not all(package in early_return_packages for package in early_return_run.required_packages)
        required_package_copy = copy(early_return_run.required_packages)
        for package in required_package_copy:
            if package.location.been_routed:
                early_return_run.required_packages.remove(package)
        assert len(early_return_run.required_packages) == 5
        early_return_run = RunPlanner.build(target_location, return_to_hub=True, focused_run=True)
        assert target_location.been_routed
        assert not early_return_run

    def test_furthest_from_hub_location_run_build(self):
        package_ids = [11, 18, 32, 31, 24, 23, 25, 26, 36, 6, 17]
        furthest_packages = _get_packages_by_id(package_ids)
        furthest_locations = PackageHandler.get_package_locations(furthest_packages)
        _set_all_locations_assigned(self.early_run_packages)
        furthest_location = self.package_hash.get_package(11).location
        furthest_location_run = RunPlanner.build(furthest_location, return_to_hub=True, focused_run=False)
        for location in furthest_location_run.ordered_route:
            print(location)
        print(furthest_location_run.delayed_location_total())
        print(furthest_location_run.assigned_truck_location_total())
        print(furthest_location_run.unconfirmed_location_total())
        print(furthest_location_run.bundled_location_total())
        print(furthest_location_run.estimated_mileage)
        print(furthest_location_run.package_total())