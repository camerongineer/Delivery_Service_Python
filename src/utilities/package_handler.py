from typing import List

from src.models import Package, Location
from src.utilities import CustomHash

__all__ = ['PackageHandler']


class PackageHandler:

    @staticmethod
    def load_packages(packages: List[Package]) -> CustomHash:
        custom_hash = CustomHash(16)
        for package in packages:
            custom_hash.add_package(package)
        return custom_hash

    @staticmethod
    def update_delivery_location(locations_list: List[Location], package: Package, updated_address: str):
        try:
            address, city, state_zip = updated_address.split(', ')
            zip_code = int(state_zip.split(' ')[1])
            for location in locations_list:
                if str(address).startswith(location.address) and location.zip_code == zip_code:
                    package.location = location
                    package.is_verified_address = True
                    return True
        except (ValueError, TypeError):
            return False
        return False
