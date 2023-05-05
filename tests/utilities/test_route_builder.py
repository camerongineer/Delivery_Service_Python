from datetime import time
from unittest import TestCase

from src import DISTANCE_CSV_FILE, CsvParser, PACKAGE_CSV_FILE, STANDARD_PACKAGE_ARRIVAL_TIME
from src.utilities.route_builder import RouteBuilder


class TestRouteBuilder(TestCase):

    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations(DISTANCE_CSV_FILE)
        self.packages = CsvParser.initialize_packages(PACKAGE_CSV_FILE, self.locations)
        self.custom_hash = RouteBuilder.load_packages(self.packages)

    def test_get_bundled_packages(self):
        package_bundles = RouteBuilder.get_bundled_packages(self.packages)
        assert len(package_bundles) == 1
        bundle = package_bundles.pop()
        assert not package_bundles
        assert len(bundle) == 6
        bundled_package_ids = [13, 14, 15, 16, 19, 20]
        for package in bundle:
            assert package.package_id in bundled_package_ids

    def test_get_delayed_packages(self):
        delayed_packages = RouteBuilder.get_delayed_packages(self.packages)
        delayed_package_ids = [6, 25, 28, 32]
        assert len(delayed_packages) == len(delayed_package_ids)
        for package in self.packages:
            if package not in delayed_packages:
                assert not str(package.special_note).startswith('Delayed')
                assert package.hub_arrival_time is STANDARD_PACKAGE_ARRIVAL_TIME
        for package_id in delayed_package_ids:
            assert self.custom_hash.get_package(package_id).hub_arrival_time == time(hour=9, minute=5)
