from enum import Enum


class Color(Enum):
    RED = '\033[91m',
    GREEN = '\033[92m',
    YELLOW = '\033[93m',
    BLUE = '\033[94m',
    MAGENTA = '\033[95m',
    CYAN = '\033[96m',

    COLOR_ESCAPE = '\033[0m'
