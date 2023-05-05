import math

import src.constants.delivery_status as delivery_status
from src.models.location import Location


class Package:
    def __init__(self, package_id: int, location: Location, is_verified_address, deadline,
                 weight, status: delivery_status, special_note):
        self.package_id = package_id
        self.location = location
        self.is_verified_address = is_verified_address
        self.deadline = deadline
        self.weight = weight
        self.status = status
        self.special_note = special_note
        self.hub_arrival_time = None
        self.hub_departure_time = None
        self.delivery_time = None

    def __hash__(self):
        return hash(self.package_id)

    def __repr__(self):
        return f"Package(package_id={self.package_id}, is_verified_address={self.is_verified_address}, deadline=datetime.strptime('{self.deadline}', '%I:%M:%S'), weight={self.weight}, status={self.status}, special_note='{self.special_note}')"

    def __eq__(self, other):
        return self.location is other.location or math.isclose((self.location.distance_dict.values()), sum(other.location.distance_dict.values()))

    def __lt__(self, other):
        return sum(self.location.distance_dict.values()) < sum(other.location.distance_dict.values())

    def __gt__(self, other):
        return sum(self.location.distance_dict.values()) > sum(other.location.distance_dict.values())

    def __le__(self, other):
        return self.location is other.location or sum(self.location.distance_dict.values()) <= sum(other.location.distance_dict.values())

    def __ge__(self, other):
        return self.location is other.location or sum(self.location.distance_dict.values()) >= sum(other.location.distance_dict.values())

    def get_id(self) -> int:
        return self.package_id

    def get_full_address(self) -> str:
        return f'{self.location}'
