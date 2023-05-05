from src.constants.utah_cities import UtahCity


class Location:
    def __init__(self, name: str, address: str, is_hub=False):
        self.name = name
        self.address = address
        self.city = None
        self.zip_code = None
        self.distance_dict = dict()
        self.is_hub = is_hub

    def set_city(self, city: UtahCity):
        self.city = city

    def set_zip_code(self, zip_code: int):
        self.zip_code = zip_code

    def set_location_as_hub(self):
        self.is_hub = True

    def set_distance_dict(self, distance_dict):
        self.distance_dict = distance_dict

    def __eq__(self, other):
        if isinstance(other, Location):
            return self.address == other.address
        return False

    def __hash__(self):
        return hash(self.address)

    def __repr__(self):
        return f"Location(name='{self.name}', address='{self.address}', is_hub={self.is_hub} zip_code={self.zip_code})"
