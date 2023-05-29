from enum import Enum


class RunFocus(Enum):
    """Enum class representing the assigned focus of a route run."""

    ASSIGNED_TRUCK = 'Focus on locations with assigned Truck ID'
    BUNDLED_PACKAGE = 'Focus on locations with bundled packages'
