from enum import Enum


class DeliveryStatus(Enum):
    AT_HUB = 'At delivery facility'
    LOADED = 'Loaded on truck'
    ON_ROUTE = 'Out for delivery'
    DELIVERED = 'Package delivered'
