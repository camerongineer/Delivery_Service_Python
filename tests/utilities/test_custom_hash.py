from datetime import time, datetime
from unittest import TestCase

from src.constants.delivery_status import DeliveryStatus
from src.constants.states import State
from src.constants.utah_cities import UtahCity
from src.models.package import Package
from src.utilities.custom_hash import _generate_index as generate_index


class TestCustomHash(TestCase):

    def setUp(self) -> None:
        self.state = State['UTAH']
        self.cities = UtahCity
        self.packages = CsvParser.initialize_packages()

    def test_generate_index_all_values(self):
        for offset in range(101):
            generated_indexes = set()
            for i in range(100000):
                index = generate_index(16, self.package, offset=offset)
                generated_indexes.add(index)

            for i in range(16):
                with self.subTest(offset=offset, value=i):
                    self.assertIn(i, generated_indexes)

    def test_add_package(self):
        self.fail()

    def test_remove_package(self):
        self.fail()
