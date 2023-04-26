from src.models.package import Package


def _generate_index(capacity: int, package: Package, offset=0):
    count = package.package_id
    for zip_code_char in str(package.zip_code):
        count += ord(zip_code_char)
    count = count * (13 ** offset)
    return count % capacity


class CustomHash:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.arr: list = [None] * capacity

    def add_package(self, package: Package):
        offset = 0
        while self.arr[_generate_index(self.capacity, package, offset=offset)]:
            offset += 1
        self.arr[_generate_index(self.capacity, package, offset=offset)] = package
        return True

    def remove_package(self):
        pass



