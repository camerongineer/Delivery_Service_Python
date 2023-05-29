from typing import final

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.models.package import Package

__all__ = ['CustomHash']


class CustomHash:

    def __init__(self, capacity: int):
        """
        Initializes a CustomHash object with the given capacity.

        Args:
            capacity (int): The capacity of the CustomHash.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        self._capacity = capacity
        self._arr: list = [[] for _ in range(capacity)]
        self._size = 0

    def __len__(self):
        """
        Returns the number of packages in the CustomHash.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        return self._size

    def __contains__(self, package):
        """
        Checks if the given package is present in the CustomHash.

        Args:
            package (Package): The package to check.

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        index = hash(package) % self._capacity
        return package in self._arr[index]

    def add_package(self, package: Package):
        """
        Adds the given package to the CustomHash.

        Args:
            package (Package): The package to add.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        if self._locate_package(package_id=package.package_id) == -1:
            self._arr[package.package_id % self._capacity].append(package)
            self._size += 1
            return True
        return False

    def get_package(self, package_id: int) -> Package:
        """
        Retrieves the package with the given package_id from the CustomHash.

        Args:
            package_id (int): The ID of the package to retrieve.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        index = self._locate_package(package_id)
        if index != -1:
            return self._arr[package_id % self._capacity][index]

    def remove_package(self, package_id: int):
        """
        Removes the package with the given package_id from the CustomHash.

        Args:
            package_id (int): The ID of the package to remove.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        index = self._locate_package(package_id)
        if index == -1:
            return False
        del self._arr[package_id % self._capacity][index]
        self._size -= 1
        return True

    def clear(self):
        """
        Clears all packages from the CustomHash.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        self._arr = [[] for _ in range(self._capacity)]
        self._size = 0

    @final
    def add_all_packages(self, packages):
        """
        Adds all packages in the given list to the CustomHash.

        Args:
            packages (List[Package]): The list of packages to add.

        Time Complexity: O(n)
        Space Complexity: O(n)
        """

        standard_arrival_time = config.STANDARD_PACKAGE_ARRIVAL_TIME
        for package in packages:
            if not package.special_note.startswith('Delayed'):
                package.update_status(DeliveryStatus.AT_HUB, standard_arrival_time)
            self.add_package(package)

    def _locate_package(self, package_id: int) -> int:
        """
        Locates the index of the package with the given package_id in the CustomHash.

        Args:
            package_id (int): The ID of the package to locate.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        for i, package in enumerate(self._arr[package_id % self._capacity]):
            if package.package_id == package_id:
                return i
        return -1
