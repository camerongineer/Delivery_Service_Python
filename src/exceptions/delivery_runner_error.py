__all__ = ['AddressUpdateException', 'DelayedPackagesArrivedException', 'PackageNotOnTruckError']


class DeliveryRunnerError(Exception):
    """Base class for exceptions in the DeliveryRunner module."""

    def __init__(self, message=None):
        """
        Initialize a DeliveryRunnerError instance.

        Args:
            message (str): The error message (default: None).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.message = message
        super().__init__(message)

    def __str__(self):
        """
        Return a string representation of the DeliveryRunnerError.

        Returns:
            str: The string representation of the error.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.message


class AddressUpdateException(DeliveryRunnerError):
    """Raised when a package address is updated and confirmed"""

    def __init__(self, package, old_location):
        """
        Initialize an AddressUpdateException instance.

        Args:
            package (Package): The updated package.
            old_location (Location): The old location of the package.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'Package #{package.package_id} | Address updated from'
                                 f' "{old_location.get_full_address()} to {package.location.get_full_address()}"')


class DelayedPackagesArrivedException(DeliveryRunnerError):
    """Raised when a delayed package has arrived"""

    def __init__(self):
        """
        Initialize a DelayedPackagesArrivedException instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'Raised when a delayed package has arrived and package can be loaded on truck')


class PackageNotOnTruckError(DeliveryRunnerError):
    """Raised when attempting to deliver package that is not on the truck"""

    def __init__(self):
        """
        Initialize a PackageNotOnTruckError instance.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        super().__init__(message=f'Delivery was attempted at a location but the package was not on the truck')
