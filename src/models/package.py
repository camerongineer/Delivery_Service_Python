import src.constants.states as states
import src.constants.utah_cities as utah_cities
import src.constants.delivery_status as delivery_status


class Package:
    def __init__(self, package_id: int, address, city: utah_cities.UtahCity, state: states.State, zip_code, is_verified_address, deadline,
                 weight, status: delivery_status, special_note):
        self.package_id = package_id
        self.address = address
        self.city = city
        self.state = state
        self.zip_code = zip_code
        self.is_verified_address = is_verified_address
        self.deadline = deadline
        self.weight = weight
        self.status = status
        self.special_note = special_note

    def __hash__(self):
        hash_str = f'{self.package_id}{self.address}{self.city}{self.state}{self.zip_code}{self.deadline}{self.weight}'
        return hash(hash_str)

    def __repr__(self):
        return f"Package(package_id={self.package_id}, address='{self.address}', city={self.city}, state={self.state}, zip_code={self.zip_code}, is_verified_address={self.is_verified_address}, deadline=datetime.strptime('{self.deadline}', '%I:%M:%S'), weight={self.weight}, status={self.status}, special_note='{self.special_note}')"

    def get_id(self) -> int:
        return self.package_id

    def get_full_address(self) -> str:
        return f'{self.address}, {self.city.value}, {self.state.abbreviation}, {self.zip_code}'
