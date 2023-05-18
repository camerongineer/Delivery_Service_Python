from src.models.truck import Truck


class RouteRun:

    def __init__(self, return_to_hub: bool):
        self.focused_run = None
        self.ordered_route: list = []
        self.required_packages = set()
        self._return_to_hub = return_to_hub
        self._estimated_mileage = 0
        self.locations = set()
        self.start_location = None
        self._target_location = None
        self._assigned_truck_id = None

    @property
    def return_to_hub(self):
        return self._return_to_hub

    @property
    def estimated_mileage(self):
        return self._estimated_mileage

    @property
    def target_location(self):
        return self._target_location

    @property
    def assigned_truck_id(self):
        return self._assigned_truck_id

    @target_location.setter
    def target_location(self, value: bool):
        self._target_location = value

    @assigned_truck_id.setter
    def assigned_truck_id(self, value: int):
        self._assigned_truck_id = value

    def package_total(self):
        return len(self.required_packages)

    def set_estimated_mileage(self):
        mileage = self.start_location.distance(self.ordered_route[0])
        for i in range(1, len(self.ordered_route)):
            mileage += self.ordered_route[i - 1].distance(self.ordered_route[i])
        if self.return_to_hub:
            mileage += self.ordered_route[len(self.ordered_route) - 1].distance(Truck.hub_location)
        self._estimated_mileage = mileage

    def assigned_truck_location_total(self):
        return len([location for location in self.ordered_route if location.has_required_truck_package])

    def delayed_location_total(self):
        return len([location for location in self.ordered_route if location.has_delayed_package_locations()])

    def bundled_location_total(self):
        return len([location for location in self.ordered_route if location.has_bundled_package])

    def unconfirmed_location_total(self):
        return len([location for location in self.ordered_route if location.has_unconfirmed_package])