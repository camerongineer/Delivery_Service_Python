from datetime import time, datetime

from src.utilities.path_utils import PathUtils

UI_ENABLED = True
UI_ELEMENTS_ENABLED = True
UI_SPEED = 100

HUB_RETURN_INSERTION_ALLOWANCE = 2.5
FILL_IN_INSERTION_ALLOWANCE = 3
CLOSEST_NEIGHBOR_MINIMUM = 8

NUM_DRIVERS = 2
NUM_DELIVERY_TRUCKS = 3
NUM_TRUCK_CAPACITY = 16
DELIVERY_TRUCK_MPH = 18.0
AVG_LOAD_TIME_PER_PACKAGE = time(second=0)
STANDARD_PACKAGE_ARRIVAL_TIME = time(hour=4, minute=00)
STANDARD_PACKAGE_LOAD_START_TIME = time(hour=6, minute=30)
PACKAGE_ARRIVAL_STATUS_UPDATE_TIME = time(hour=6, minute=00)
PACKAGE_LOAD_SPEED_MAX_SECONDS = 100
DELIVERY_DISPATCH_TIME = time(hour=8, minute=00)
DELIVERY_RETURN_TIME = time(hour=19, minute=00)
DELIVERY_DATE = datetime.min

DISTANCE_CSV_FILE = PathUtils.get_full_file_path('distance_table.csv')
PACKAGE_CSV_FILE = PathUtils.get_full_file_path('package_file.csv')

EXCEPTED_UPDATES = dict()
PACKAGE_9_ADDRESS_CHANGE_TIME = time(hour=10, minute=20)
PACKAGE_9_UPDATED_ADDRESS = "410 S State St., Salt Lake City, UT 84111"
EXCEPTED_UPDATES[9] = {'update_time': PACKAGE_9_ADDRESS_CHANGE_TIME, 'address': PACKAGE_9_UPDATED_ADDRESS}
