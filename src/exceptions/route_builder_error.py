from src import config
from src.models.package import Package

__all__ = ['LateDeliveryError', 'PackageNotArrivedError']


class RouteBuilderError(Exception):
    """Base class for exceptions in the RouteBuilder module."""

    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


class LateDeliveryError(RouteBuilderError):
    """Raised when a package is routed to a time that will result in a late delivery"""

    def __init__(self, package: Package):
        super().__init__(message=f'This route plan results in a late delivery at "{package.location.name}"'
                                 f' at "{package.location.address} | Package ID: {package.package_id}')


class PackageNotArrivedError(RouteBuilderError):
    """Raised when a package is routed to a time that results in being loaded on a truck before it arrives at the hub"""

    def __init__(self, package: Package):
        super().__init__(message=f'This route plan results in a package being loaded before it has arrived at the hub '
                                 f'| Package ID: {package.package_id}')


class TruckCapacityExceededError(RouteBuilderError, capacity=config.NUM_TRUCK_CAPACITY):
    """Raised when the number of packages allowed on a truck is exceeded"""

    def __init__(self, package: Package):
        super().__init__(message=f'This route plan results truck being loaded over the allowed capacity '
                                 f'| Package ID: {package.package_id}')
