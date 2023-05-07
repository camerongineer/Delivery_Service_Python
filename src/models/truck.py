from src import config
from src.models import Package
from src.utilities import custom_hash

__all__ = ['Truck']


class Truck(custom_hash.CustomHash):
    id_count = 1

    def __init__(self):
        super().__init__(config.NUM_TRUCK_CAPACITY)
        self._has_driver = False
        self._truck_id = Truck.id_count
        self._mileage = 0
        self._stopped = True

    def add_package(self, package: Package):
        if self._size >= config.NUM_TRUCK_CAPACITY:
            pass
            #print('Truck is at maximum capacity')
        super().add_package(package)

    @property
    def has_driver(self):
        return self._has_driver

    @has_driver.setter
    def has_driver(self, value):
        if value:
            self._has_driver = True
        else:
            self._has_driver = False

    @property
    def truck_id(self):
        return self._truck_id

    @truck_id.setter
    def truck_id(self, value):
        self._truck_id = Truck.id_count
        Truck.id_count += 1
