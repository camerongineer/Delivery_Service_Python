from datetime import time
from unittest import TestCase

from src import config
from src.models.truck import Truck
from src.utilities.custom_hash import CustomHash
from src.utilities.package_handler import PackageHandler
from src.utilities.route_builder import RouteBuilder, _find_earliest_deadline_packages


class TestRouteBuilder(TestCase):

    def setUp(self) -> None:
        self.locations = PackageHandler.all_locations
        self.packages = PackageHandler.all_packages
        self.custom_hash = CustomHash(config.NUM_TRUCK_CAPACITY)
        self.custom_hash.add_all_packages(self.packages)

    def test_get_optimized_route(self):

        truck_1 = Truck(1)
        truck_2 = Truck(2)
        truck_1.partner = truck_2
        truck_2.partner = truck_1
        print(truck_2.partner.current_location)
        print(truck_1.partner.current_location)
        truck_2.dispatch(config.DELIVERY_DISPATCH_TIME)
        packages = PackageHandler.get_delayed_packages().union(
            PackageHandler.get_assigned_truck_packages(truck_2.truck_id))

        RouteBuilder.get_optimized_route(truck_2, in_location_package_dict=PackageHandler.get_location_package_dict(
            self.packages))
        # truck_2.pause(time(hour=9), time(hour=9, minute=30))
        if len(RouteBuilder.get_routed_locations()) + 1 == len(
                self.locations) and Truck.hub_location not in RouteBuilder.get_routed_locations():
            print("ROUTING COMPLETE")
        for mile, (stop_time, last_location, current_location, next_location) in truck_2._travel_ledger.items():
            print(
                f'miles={round(mile, ndigits=1)}, time={stop_time}, location={current_location.name}, address={current_location.address}')
        # print(len(truck_2._travel_ledger))
        # current_time = time(9, 47, 20)
        # print(truck_2.get_current_location(current_time))
        # print(truck_2.completion_time)
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

    def test_build_optimized_runs(self):
        RouteBuilder.build_optimized_runs()
