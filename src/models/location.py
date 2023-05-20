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
        self._city = None
        self._zip_code = None
        self.distance_dict = dict()
        self.package_set = set()
        self.is_hub = is_hub
        self.been_visited = False
        self.been_assigned = False
        self.been_routed = False
        self.assigned_truck = None
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
        return f"Location(name='{self.name}', address='{self.address}', is_hub={self.is_hub} zip_code={self.zip_code}, been_assigned={self.been_assigned})"

    @property
    def city(self):
        return self._city

    @property
    def zip_code(self):
        return self._zip_code

    @city.setter
    def city(self, value: UtahCity):
        self._city = value

    @zip_code.setter
    def zip_code(self, value: int):
        self._zip_code = value

    def set_zip_code(self, zip_code: int):
        self.zip_code = zip_code

    def set_location_as_hub(self):
        self.is_hub = True

    def set_distance_dict(self, distance_dict):
        self.distance_dict = distance_dict

    def set_earliest_deadline(self, deadline: time):
        self.earliest_deadline = deadline

    def has_close_deadline(self, current_time, time_delta=1800):
        if not self.earliest_deadline:
            return False
        return TimeConversion.is_time_at_or_before_other_time(self.earliest_deadline,
                                                              TimeConversion.add_time_delta(current_time, time_delta))

    def has_delayed_packages(self):
        if not self.latest_package_arrival:
            return False
        return self.latest_package_arrival != config.STANDARD_PACKAGE_ARRIVAL_TIME

    def has_early_deadline(self):
        if not self.earliest_deadline:
            return False
        return self.earliest_deadline != config.DELIVERY_RETURN_TIME

    def package_total(self):
        if not self.package_set:
            return 0
        return len(self.package_set)

    def distance(self, other_location):
        if self is other_location:
            return None
        return self.distance_dict[other_location]