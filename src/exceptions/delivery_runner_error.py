__all__ = ['PackageNotOnTruckError']


class DeliveryRunnerError(Exception):
    """Base class for exceptions in the DeliveryRunner module."""

    def __init__(self, message=None):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message


class PackageNotOnTruckError(DeliveryRunnerError):
    """Raised when attempting to deliver package that is not on the truck"""

    def __init__(self):
        super().__init__(message=f'Delivery was attempted at a location but the package was not on the truck')
