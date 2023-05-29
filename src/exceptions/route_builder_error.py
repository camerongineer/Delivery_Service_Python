from src import config

__all__ = ['BundledPackageTruckAssignmentError', 'InvalidRouteRunError', 'LateDeliveryError', 'OptimalHubReturnError',
           'OverlappingRouteRunError', 'PackageNotArrivedError', 'TruckCapacityExceededError',
           'UnconfirmedPackageDeliveryError']


class RouteBuilderError(Exception):
    """Base class for exceptions in the RouteBuilder module."""

    def __init__(self, message=None):
        """
        Initialize a RouteBuilderError instance.

        Args:
            message (str): The error message (default: None).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.message = message
        super().__init__(message)

    def __str__(self):
        """
        Return a string representation of the RouteBuilderError.

        Returns:
            str: The string representation of the error.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.message


class LateDeliveryError(RouteBuilderError):
    """Raised when a package is routed to a time that will result in a late delivery"""

    def __init__(self):
        """
        Initialize a LateDeliveryError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This route plan results in a late delivery')


class UnconfirmedPackageDeliveryError(RouteBuilderError):
    """Raised when a package is routed to a time that will result in a delivery while a package is unconfirmed"""

    def __init__(self):
        """
        Initialize an UnconfirmedPackageDeliveryError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This route plan results in a delivery to a location with unconfirmed packages')


class PackageNotArrivedError(RouteBuilderError):
    """Raised when a package is routed to a time that results in being loaded on a truck before it arrives at the hub"""

    def __init__(self):
        """
        Initialize a PackageNotArrivedError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This route plan results in a package being loaded before it has arrived at the hub')


class TruckCapacityExceededError(RouteBuilderError):
    """Raised when the number of packages allowed on a truck is exceeded"""

    def __init__(self, capacity=config.NUM_TRUCK_CAPACITY):
        """
        Initialize a TruckCapacityExceededError instance.

        Args:
            capacity (int): The truck capacity (default: config.NUM_TRUCK_CAPACITY).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self._capacity = capacity
        super().__init__(message=f'This route plan results truck being loaded over the allowed capacity: {capacity}')


class InvalidRouteRunError(RouteBuilderError):
    """Raised when route run is created with 2 different assigned trucks ids"""

    def __init__(self):
        """
        Initialize an InvalidRouteRunError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This route plan results in route run with locations assigned to 2 different trucks')


class OverlappingRouteRunError(RouteBuilderError):
    """Raised when route runs assigned to the same truck are overlapping"""

    def __init__(self):
        """
        Initialize an OverlappingRouteRunError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This route plan results in route runs assigned to the same truck are have'
                                 f' overlapping start and/or end times')


class BundledPackageTruckAssignmentError(RouteBuilderError):
    """Raised when bundled packages and locations are not given an assigned truck once any of them are assigned"""

    def __init__(self):
        """
        Initialize a BundledPackageTruckAssignmentError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This Route Run must be assigned at truck id does not assign all'
                                 f' bundled packages to the same truck if any are assigned')


class OptimalHubReturnError(RouteBuilderError):
    """Raised when truck will be in close vicinity of hub and the truck is less than half empty"""

    def __init__(self):
        """
        Initialize an OptimalHubReturnError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'This Route Run results in the truck not returning to the hub when the truck'
                                 f'close and the truck would be more than half empty')
