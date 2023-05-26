from src.ui import UI
from src.utilities.delivery_runner import DeliveryRunner


def main():
    DeliveryRunner.load_trucks()
    DeliveryRunner.commence_deliveries()
    UI.menu()


if __name__ == "__main__":
    main()
