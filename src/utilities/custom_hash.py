from src.models.package import Package


class CustomHash:
    _hash_id = 1

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.arr: list = [[]] * capacity
        self._size = 0
        self.id = CustomHash._hash_id
        CustomHash._hash_id += 1

    def __len__(self):
        return self._size

    def add_package(self, package: Package):
        if self._locate_package(package_id=package.package_id) == -1:
            self.arr[package.package_id % self.capacity].append(package)
            self._size += 1
            return True
        return False

    def get_package(self, package_id: int) -> Package:
        index = self._locate_package(package_id)
        if index != -1:
            return self.arr[package_id % self.capacity][index]

    def remove_package(self, package_id: int):
        index = self._locate_package(package_id)
        if index == -1:
            return False
        del self.arr[package_id % self.capacity][index]
        self._size -= 1
        return True

    def _locate_package(self, package_id: int) -> int:
        for i, package in enumerate(self.arr[package_id % self.capacity]):
            if package.package_id == package_id:
                return i
        return -1
