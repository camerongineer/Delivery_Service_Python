from copy import copy
from unittest import TestCase

from src import config
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
        truck = Truck(1)
        early_return_packages = PackageHandler.get_bundled_packages()
        target_package = self.package_hash.get_package(15)
        target_location = target_package.location
        early_return_run = RunPlanner.build(target_location, truck)

        assert len(early_return_run.ordered_route) == 6
        assert early_return_run.ordered_route[0].is_hub
        assert early_return_run.ordered_route[-1].is_hub
        assert target_location in early_return_run.ordered_route
        assert (sum([location.package_total() for location in early_return_run.ordered_route]) ==
                len(self.packages) % config.NUM_TRUCK_CAPACITY)
        assert len(early_return_run.required_packages) == 11
        assert all(package in early_return_run.required_packages for package in early_return_packages)
        assert not all(package in early_return_packages for package in early_return_run.required_packages)
        required_package_copy = copy(early_return_run.required_packages)
        for package in required_package_copy:
            if package.location.been_assigned:
                early_return_run.required_packages.remove(package)
        assert len(early_return_run.required_packages) == 3
        early_return_run = RunPlanner.build(target_location, truck)
        assert target_location.been_assigned
        assert not early_return_run
