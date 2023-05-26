import math
from copy import copy
from datetime import time

__all__ = ['Package']

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.location import Location


def _get_formatted_status_string(update, package, formatted_address, status):
    return (f'{update} | Package ID: {str(package.package_id).zfill(2)} |'
            f' Destination: {formatted_address} | Status: "{status}"')


class Package:
    def __init__(self, package_id: int, location: Location, is_verified_address, deadline, weight, special_note):
        self.package_id = package_id
        self.location = location
        self.is_verified_address = is_verified_address
        self.deadline = deadline
        self.weight = weight
        self.status = DeliveryStatus.ON_ROUTE_TO_DEPOT
        self.special_note = special_note
        self.status_update_dict = dict()
        self.bundled_package_set = set()
        self.assigned_truck_id = None
        self.bundled_package_ids = None
        self.pending_update_time = None
        self.hub_arrival_time = None
        self.hub_departure_time = None
        self.delivery_time = None

    def __hash__(self):
        return hash(self.package_id)

    def __str__(self):
        return f'Package ID: {self.package_id}\n' \
               f'Location Name: {self.location.name}\n' \
               f'Address: {self.location.get_full_address()}\n' \
               f'Delivery Deadline: {self.deadline}\n' \
               f'Weight: {self.weight} ' + ('lbs.' if self.weight != 1 else 'lb.') + '\n' \
               f'Verified Address: ' + ("Yes" if self.is_verified_address else "No") + \
               (f'\nSpecial Notes: {self.special_note}' if self.special_note else '')

    def __repr__(self):
        return f"Package(package_id={self.package_id}, Location: {self.location.name} - {self.location.address}" \
               f" - is_verified_address={self.is_verified_address}," \
               f" deadline=datetime.strptime('{self.deadline}', '%I:%M:%S'), weight={self.weight}," \
               f" status={self.status}, special_note='{self.special_note}')"

    def __eq__(self, other):
        return self.location is other.location or \
            math.isclose((self.location.distance_dict.values()), sum(other.location.distance_dict.values()))

    def __lt__(self, other):
        return sum(self.location.distance_dict.values()) < sum(other.location.distance_dict.values())

    def __gt__(self, other):
        return sum(self.location.distance_dict.values()) > sum(other.location.distance_dict.values())

    def __le__(self, other):
        return self.location is other.location or \
            sum(self.location.distance_dict.values()) <= sum(other.location.distance_dict.values())

    def __ge__(self, other):
        return self.location is other.location or \
            sum(self.location.distance_dict.values()) >= sum(other.location.distance_dict.values())

    def get_id(self) -> int:
        return self.package_id

    def update_status(self, updated_status: DeliveryStatus, current_time: time):
        self.status = updated_status
        if current_time not in self.status_update_dict:
            self.status_update_dict[current_time] = {'status': copy(updated_status), 'location': self.location,
                                                     'is_verified_address': self.is_verified_address,
                                                     'special_note': self.special_note}
        else:
            if self.status_update_dict[current_time]['status'] is not updated_status:
                if (isinstance(self.status_update_dict[current_time]['status'], tuple) and
                        updated_status not in self.status_update_dict[current_time]['status']):
                    self.status_update_dict[current_time]['status'] += (updated_status,)
                else:
                    self.status_update_dict[current_time]['status'] =\
                        self.status_update_dict[current_time]['status'], updated_status

    def get_full_address(self) -> str:
        return f'{self.location}'

    def get_status_string(self, current_time, address_length=None):
        if current_time:
            last_update, package_state = self.find_package_state_at_time(current_time)
            status = package_state['status']
            location = package_state['location']
        else:
            status = self.status
            location = self.location
            last_update = list(self.status_update_dict.keys())[-1]
        address = location.get_full_address()
        if not address_length:
            address_length = max([len(_location.get_full_address()) for _location in [location, self.location]])
        formatted_address = ('{:^' + str(address_length) + '}').format(address)
        if isinstance(status, tuple):
            appended_status = []
            for tuple_status in reversed(status):
                appended_status.append(_get_formatted_status_string(last_update, self, formatted_address, tuple_status))
            return '\n'.join(appended_status)
        return _get_formatted_status_string(last_update, self, formatted_address, status)

    def find_package_state_at_time(self, current_time: time):
        latest_update_time = config.STANDARD_PACKAGE_ARRIVAL_TIME
        for update_time, values in self.status_update_dict.items():
            if current_time >= update_time:
                latest_update_time = update_time
                continue
            else:
                break
        return latest_update_time, self.status_update_dict[latest_update_time]
