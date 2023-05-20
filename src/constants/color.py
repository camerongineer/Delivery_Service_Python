from enum import Enum


class Color(Enum):
    RED = '\033[31m',
    GREEN = '\033[32m',
    YELLOW = '\033[33m',
    BLUE = '\033[34m',
    MAGENTA = '\033[35m',
    CYAN = '\033[36m',

    COLOR_ESCAPE = '\033[0m'
