from datetime import time
from unittest import TestCase

from src import config
from src.models.truck import Truck
from src.utilities.custom_hash import CustomHash
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder


class TestRouteBuilder(TestCase):

    def setUp(self) -> None:
        self.locations = PackageHandler.all_locations
        self.packages = PackageHandler.all_packages
        self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
        for package in self.packages:
            self.custom_hash.add_package(package)

    def test_get_optimized_route(self):
        truck = Truck(2)
        truck.dispatch_time = time(hour=9, minute=5)
        packages = PackageHandler.get_delayed_packages().union(PackageHandler.get_assigned_truck_packages(truck.truck_id))

        # truck.pause(time(hour=8, minute=20), time(hour=8, minute=55))
        # truck.pause(time(hour=8, minute=14), time(hour=9, minute=19))
        # truck.pause(time(hour=8, minute=57), time(hour=8, minute=59))
        RouteBuilder.get_optimized_route(truck, in_location_package_dict=PackageHandler.get_location_package_dict(self.packages), route_start_time=time(hour=9, minute=5))
        # truck.pause(time(hour=9), time(hour=9, minute=30))
        if len(RouteBuilder.get_routed_locations()) + 1 == len(self.locations) and Truck.hub_location not in RouteBuilder.get_routed_locations():
            print("ROUTING COMPLETE")
        for mile, (stop_time, last_location, current_location, next_location) in truck._travel_ledger.items():
            print(f'miles={round(mile, ndigits=1)}, time={stop_time}, location={current_location.name}, address={current_location.address}')
        # print(len(truck._travel_ledger))
        # current_time = time(9, 47, 20)
        # print(truck.get_current_location(current_time))
        # print(truck.completion_time)
        # for package in self.packages:
        #     print(package.status_update_dict)

    def test_get_routed_locations(self):
        assert len(RouteBuilder.get_routed_locations()) == 0
        self.locations[0].been_routed = True
        assert len(RouteBuilder.get_routed_locations()) == 1
        assert RouteBuilder.get_routed_locations().pop() is self.locations[0]
        self.locations[0].been_routed = False
        self.locations[1].been_routed = True
        assert len(RouteBuilder.get_routed_locations()) == 1
        self.locations[1].been_routed = False
        assert len(RouteBuilder.get_routed_locations()) == 0
