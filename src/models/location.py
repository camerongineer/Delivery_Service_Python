__all__ = ['Location']

from datetime import time

from src import config
from src.config import DELIVERY_RETURN_TIME
from src.constants.utah_cities import UtahCity
from src.utilities.time_conversion import TimeConversion


class Location:
    def __init__(self, name: str, address: str, is_hub=False):
        self.name = name
        self.address = address
        self.city = None
        self.zip_code = None
        self.distance_dict = dict()
        self.package_set = set()
        self.is_hub = is_hub
        self.been_visited = False
        self.been_assigned = False
        self.been_routed = False
        self.earliest_deadline = DELIVERY_RETURN_TIME
        self.latest_package_arrival = None
        self.has_required_truck_package = False
        self.has_unconfirmed_package = False
        self.has_bundled_package = False

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.address == other.address and self.name == other.name and self.zip_code == other.zip_code
        return False

    def __hash__(self):
        return hash(self.address + self.name)

    def __contains__(self, item):
        return item in self.package_set

    def __repr__(self):
        return f"Location(name='{self.name}', address='{self.address}', is_hub={self.is_hub} zip_code={self.zip_code})"

    def set_city(self, city: UtahCity):
        self.city = city

    def set_zip_code(self, zip_code: int):
        self.zip_code = zip_code

    def set_location_as_hub(self):
        self.is_hub = True

    def set_distance_dict(self, distance_dict):
        self.distance_dict = distance_dict

    def set_earliest_deadline(self, deadline: time):
        self.earliest_deadline = deadline

    def has_close_deadline(self, current_time, time_delta=1800):
        return TimeConversion.is_time_at_or_before_other_time(self.earliest_deadline,
                                                              TimeConversion.add_time_delta(current_time, time_delta))

    def has_delayed_package_locations(self):
        return not TimeConversion.is_time_at_or_before_other_time(self.latest_package_arrival,
                                                                  config.STANDARD_PACKAGE_ARRIVAL_TIME)

    def package_total(self):
        return len(self.package_set)

    def distance(self, other_location):
        if self is other_location:
            return None
        return self.distance_dict[other_location]