import os
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

DISTANCE_CSV_FILE = os.path.join(PathUtils.get_project_root(), 'distance_table.csv')
PACKAGE_CSV_FILE = os.path.join(PathUtils.get_project_root(), 'package_file.csv')
