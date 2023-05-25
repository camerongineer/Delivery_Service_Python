from src.utilities.delivery_runner import DeliveryRunner


def main():
    DeliveryRunner.load_trucks()
    DeliveryRunner.commence_deliveries()


# Entry point of the script
if __name__ == "__main__":
    main()
