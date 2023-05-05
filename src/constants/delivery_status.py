from enum import Enum


class DeliveryStatus(Enum):
    ON_ROUTE_TO_DEPOT = 'On route to delivery facility'
    AT_HUB = 'At delivery facility'
    LOADED = 'Loaded on truck'
    OUT_FOR_DELIVERY = 'Out for delivery'
    DELIVERED = 'Package delivered'
