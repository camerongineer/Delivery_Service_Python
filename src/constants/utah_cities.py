from enum import Enum


__all__ = ['UtahCity']

from src.constants.states import State


class UtahCity(Enum):
    HOLLADAY = ('Holladay', [84117])
    MILLCREEK = ('Millcreek', [84117])
    MURRAY = ('Murray', [84107, 84121])
    SALT_LAKE_CITY = ('Salt Lake City', [84103, 84104, 84105, 84106, 84111, 84115, 84117, 84118, 84119, 84123])
    WEST_VALLEY_CITY = ('West Valley City', [84119])

    def __init__(self, displayed_name, zip_codes: list, state=State.UTAH):
        self.displayed_name = displayed_name
        self.zip_codes = zip_codes
        self.state = state
