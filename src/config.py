from datetime import time

from src.utilities.path_utils import PathUtils

NUM_DRIVERS = 2
NUM_DELIVERY_TRUCKS = 3
NUM_TRUCK_CAPACITY = 16
DELIVERY_TRUCK_MPH = 18.0
AVG_LOAD_TIME_PER_PACKAGE = time(second=0)
STANDARD_PACKAGE_ARRIVAL_TIME = time(hour=4, minute=00)
PACKAGE_ARRIVAL_STATUS_UPDATE_TIME = time(hour=6, minute=00)
DELIVERY_DISPATCH_TIME = time(hour=8, minute=00)
DELIVERY_RETURN_TIME = time(hour=19, minute=00)

DISTANCE_CSV_FILE = PathUtils.get_full_path_string('distance_table.csv')
PACKAGE_CSV_FILE = PathUtils.get_full_path_string('package_file.csv')
