from unittest import TestCase

from src import config
from src.constants.delivery_status import DeliveryStatus
from src.utilities.delivery_runner import DeliveryRunner
from src.utilities.package_handler import PackageHandler


class TestDeliveryRunner(TestCase):

    def test_load_trucks(self):
        config.UI_ENABLED = False
        config.UI_ELEMENTS_ENABLED = False
        DeliveryRunner.load_trucks()
        assert all(package.status != DeliveryStatus.LOADED for package in PackageHandler.get_delayed_packages())
