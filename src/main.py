from src.ui import UI
from src.utilities.delivery_runner import DeliveryRunner


def main():
    """
    Main function for the delivery program.
    - Loads the trucks.
    - Commences the deliveries.
    - Displays the user interface menu.

    Time Complexity: O(n^2 * m)
    Space Complexity: O(n^2)
    """

    DeliveryRunner.load_trucks()
    DeliveryRunner.commence_deliveries()
    UI.menu()


if __name__ == "__main__":
    main()
