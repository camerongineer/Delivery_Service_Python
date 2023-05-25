from unittest import TestCase

from src import config
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder


class TestRouteBuilder(TestCase):

    def test_build_optimized_runs(self):
        config.UI_ENABLED = False
        RouteBuilder.build_optimized_runs()
        assert not [location for location in PackageHandler.all_locations if not location.been_assigned]
