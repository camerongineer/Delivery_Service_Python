from src.ui import UI
from src.utilities.delivery_runner import DeliveryRunner


def main():
    """
    Main function for the delivery program.
    - Loads the trucks.
    - Commences the deliveries.
    - Displays the user interface menu.

    """

    DeliveryRunner.load_trucks()
    DeliveryRunner.commence_deliveries()
    UI.menu()


if __name__ == "__main__":
    main()
