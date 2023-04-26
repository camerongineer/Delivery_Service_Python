import os
from datetime import time

from src.utilities.path_utils import PathUtils

DELIVERY_DISPATCH_TIME = time(hour=8, minute=00)
DELIVERY_RETURN_TIME = time(hour=19, minute=00)
DISTANCE_CSV_FILE = os.path.join(PathUtils.get_project_root(), 'distance_table.csv')
PACKAGE_CSV_FILE = os.path.join(PathUtils.get_project_root(), 'package_file.csv')
