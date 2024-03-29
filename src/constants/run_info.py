from enum import Enum


class RunInfo(Enum):
    """Enum class representing information accessed in the run analysis dictionary of a route run"""

    PREVIOUS_LOCATION = 'Previous location of the run'
    MILES_FROM_PREVIOUS = 'Mile away from previous location'
    ESTIMATED_MILEAGE = 'Estimated mileage at arrival'
    ESTIMATED_TIME = 'Estimated time of arrival'
    NEXT_LOCATION = 'Next location of the run'
    MILES_TO_NEXT = 'Mile away from next location'
    ESTIMATED_MILEAGE_AT_NEXT = 'Estimated mileage at next location'
    ESTIMATED_TIME_AT_NEXT = 'Estimated time at next location'
    LATEST_ALLOWED_DELIVERY_TIME = 'Earliest deadline of the location'
    LATEST_ALLOWED_HUB_DEPARTURE = 'Latest package arrival at hub'
    UNDELIVERED_PACKAGES_TOTAL = 'Number of undelivered package in the run'
    DEPARTURE_REQUIREMENT_MET = 'Departure requirement met'
    DELIVERY_TIME_REQUIREMENT_MET = 'Delivery time requirement met'
    PACKAGES_DELIVERED = 'Packages delivered'
    LOCATIONS_VISITED = 'Locations visited'
    ESTIMATED_MILEAGE_TO_HUB = 'Estimated mileage to hub'
    ESTIMATED_TIME_OF_HUB_ARRIVAL = 'Estimated time of hub arrival'
    MILES_FROM_PREVIOUS_WITH_HUB_INSERT = 'Miles from previous location with hub insert'
    DIFFERENCE = 'Difference'
    IS_VALID_RUN_AT_LOCATION = 'Validity of run at location'
    OPTIMAL_HUB_DEPARTURE_TIME = 'Optimal hub departure time'
    MINIMUM_OPTIMAL_TIME_AT_LOCATION = 'Minimum optimal start time at location'
    ERROR_TYPE = 'Error type'
    ERROR_LOCATION = 'Location where the error occurred in the run'
