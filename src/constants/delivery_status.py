from enum import Enum

__all__ = ['DeliveryStatus']

from src.constants.color import Color


class DeliveryStatus(Enum):
    ON_ROUTE_TO_DEPOT = 'On route to delivery facility', Color.RED
    AT_HUB = 'At delivery facility', Color.WHITE
    LOADED = 'Loaded on truck', Color.BLUE
    OUT_FOR_DELIVERY = 'Out for delivery', Color.YELLOW
    DELIVERED = 'Package delivered', Color.GREEN

    def __init__(self, description, color):
        self.description = description
        self.color = color

    def __str__(self):
        return self.description

    def __repr__(self):
        return self.description
