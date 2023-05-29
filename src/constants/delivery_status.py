from enum import Enum

__all__ = ['DeliveryStatus']

from src.constants.color import Color


class DeliveryStatus(Enum):
    """Enum class representing the delivery status of a package."""

    ON_ROUTE_TO_DEPOT = 'On route to delivery facility', Color.RED
    AT_HUB = 'At delivery facility', Color.WHITE
    LOADED = 'Loaded on truck', Color.BLUE
    OUT_FOR_DELIVERY = 'Out for delivery', Color.YELLOW
    DELIVERED = 'Package delivered', Color.GREEN

    def __init__(self, description, color):
        """
        Initialize a DeliveryStatus instance.

        Args:
            description (str): The description of the delivery status.
            color (Color): The color associated with the delivery status.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        self.description = description
        self.color = color

    def __str__(self):
        """
        Return a string representation of the DeliveryStatus.

        Returns:
            str: The string representation of the delivery status.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.description

    def __repr__(self):
        """
        Return a string representation of the DeliveryStatus.

        Returns:
            str: The string representation of the delivery status.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self.description
