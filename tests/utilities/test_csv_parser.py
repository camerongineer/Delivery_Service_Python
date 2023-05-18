from datetime import time, datetime
from unittest import TestCase

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.constants.states import State
from src.constants.utah_cities import UtahCity
from src.models.location import Location
from src.utilities.csv_parser import CsvParser
from src.utilities.time_conversion import TimeConversion


class TestCsvParser(TestCase):
    def setUp(self) -> None:
        self.locations = CsvParser.initialize_locations()
        self.packages = CsvParser.initialize_packages(self.locations)

    def test_initialize_packages(self):
        for package in self.packages:
            assert package.package_id and isinstance(package.package_id, int)
            assert package.location and isinstance(package.location, Location)
            assert package.location.city and isinstance(package.location.city, UtahCity)
            assert package.location.city.state and isinstance(package.location.city.state, State)
            assert package.deadline and isinstance(package.deadline, time)
            assert package.weight and isinstance(package.weight, int)
            assert package.status is DeliveryStatus.ON_ROUTE_TO_DEPOT if\
                   package.special_note.startswith('Delayed') else DeliveryStatus.AT_HUB
            assert package.bundled_package_ids if package.special_note.startswith('Must be delivered with') else \
                not package.bundled_package_ids
            if package.special_note.startswith('Delayed'):
                assert package.hub_arrival_time != config.STANDARD_PACKAGE_ARRIVAL_TIME
            else:
                assert package.hub_arrival_time == config.STANDARD_PACKAGE_ARRIVAL_TIME
            assert package.assigned_truck_id \
                if package.special_note.startswith('Can only be on truck ') else not package.assigned_truck_id
            assert TimeConversion.get_datetime(package.location.earliest_deadline) <= \
                   TimeConversion.get_datetime(package.deadline)
            assert TimeConversion.get_datetime(package.location.latest_package_arrival) >= \
                   TimeConversion.get_datetime(package.hub_arrival_time)
            assert package in package.location



    def test_initialize_locations(self):
        hubs = 0
        for location in self.locations:
            if location.is_hub:
                hubs += 1
            assert location.name and isinstance(location.name, str)
            assert location.address and isinstance(location.address, str)
            assert location.zip_code and isinstance(location.zip_code, int)
            assert len(location.distance_dict.keys()) == len(self.locations) - 1
            for dist_location, distance in location.distance_dict.items():
                assert dist_location and isinstance(dist_location, Location)
                assert distance and isinstance(distance, float)
        assert hubs == 1

    def test_all_other_locations_in_location_dict(self):
        for location in self.locations:
            total_in_location_dict = 0
            for other_location in location.distance_dict.keys():
                assert other_location is not location
                if other_location in location.distance_dict.keys():
                    total_in_location_dict += 1
            assert total_in_location_dict == len(self.locations) - 1
