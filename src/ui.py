import re
from time import sleep
from datetime import time

from src import config
from src.constants.color import Color
from src.utilities.package_handler import PackageHandler


def _simulation():
    """
    Performs the simulation and displays a completion message.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    UI.print(f'\n\n\nSimulation complete', think=True, color=Color.RED, sleep_seconds=6, log_enabled=False)
    _clear()


def _clear():
    """
    Clears the console by printing new lines.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    for i in range(100):
        print()


def _retrieve_status_of_all_packages():
    """
    Retrieves the status of all packages and displays them.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    _clear()
    address_length = max([len(location.get_full_address()) for location in PackageHandler.all_locations])
    for i in range(1, len(PackageHandler.all_packages) + 1):
        snapshot_package = PackageHandler.get_package_snapshot(PackageHandler.package_hash.get_package(i),
                                                               target_time=UI.TIME)
        color = (snapshot_package.status.color if not isinstance(snapshot_package.status, tuple) else
                 snapshot_package.status[-1].color)
        UI.print(snapshot_package.get_status_string(UI.TIME, address_length=address_length), sleep_seconds=.25,
                 color=color, log_enabled=False)
    UI.press_enter_to_continue()
    _clear()


def _retrieve_package_details():
    """
    Retrieves the details of a specific package.

    Time Complexity: O(n log n)
    Space Complexity: O(n)
    """

    while True:
        _clear()
        UI.print('Please enter the ID number of the package', log_enabled=False)
        try:
            package_id = int(input('ENTER ID NUMBER -> '))
            package = PackageHandler.package_hash.get_package(package_id)
            if not package:
                raise ValueError
            snapshot_package = PackageHandler.get_package_snapshot(package, UI.TIME)
            UI.print('\n\n' + (str(snapshot_package)), log_enabled=False)
            UI.print('\n' + UI.UNDERLINE + 'Status Updates' + Color.COLOR_ESCAPE.value,
                     log_enabled=False, extra_lines=1, color=Color.YELLOW)
            for update_time, info in reversed(list(snapshot_package.status_update_dict.items())):
                if UI.TIME < update_time:
                    continue
                UI.print(snapshot_package.get_status_string(update_time), log_enabled=False)
            UI.press_enter_to_continue()
            _clear()
            return
        except (TypeError, ValueError):
            UI.print('\nINVALID OPTION\n', color=Color.RED, sleep_seconds=2, log_enabled=False)
            _clear()


def _time_machine():
    """
    Allows the user to input a time to transport to.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    _clear()
    while True:
        UI.print(f'Please input a time below between "04:00"-"18:59" that you would like to be transport to',
                 color=Color.YELLOW, sleep_seconds=1, log_enabled=False)
        user_input = input('~EXAMPLE -> 12:45 | CHOOSE A TIME -> ')
        if not re.match(r"^(0?[4-9]|1[0-8]):[0-5][0-9]$", user_input.strip()):
            UI.print('\nINVALID OPTION\n', color=Color.RED, sleep_seconds=2, log_enabled=False)
            _clear()
        else:
            hour, minute = map(int, user_input.split(":"))
            UI.TIME = time(hour=hour, minute=minute)
            UI.print('Transporting', think=True, color=Color.RED, sleep_seconds=1, log_enabled=False)
            _clear()
            return


def _view_log():
    """
    Displays the log file.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    UI.print('Transporting to end of day', think=True, color=Color.RED, sleep_seconds=1, log_enabled=False)
    print('\n\n')
    for line in UI.LOG_FILE.splitlines():
        print(line)
        sleep(.025)
    UI.press_enter_to_continue()
    print('\n\n')
    UI.print('Transporting to previous time', think=True, color=Color.RED, sleep_seconds=1, log_enabled=False)
    print('\n\n')
    if config.UI_ELEMENTS_ENABLED:
        _clear()


def _adjust_ui_speed():
    """
    Allows the user to adjust the UI speed.

    Time Complexity: O(1)
    Space Complexity: O(1)
    """

    _clear()
    UI.print(UI.UNDERLINE + f'Current Speed: {UI.SPEED // 100}' + Color.COLOR_ESCAPE.value)
    while True:
        try:
            speed = int(input('Please choose a speed [1-9]: '))
            if 0 < speed < 10:
                if (UI.SPEED // 100) == speed:
                    UI.print(f'\nSpeed not changed', sleep_seconds=2, log_enabled=False, color=Color.YELLOW)
                else:
                    UI.print(f'\nSpeed Changed to {speed}!', sleep_seconds=2, log_enabled=False, color=Color.GREEN)
                    UI.SPEED = int(speed * 100)
                _clear()
                return
            raise TypeError
        except TypeError:
            UI.print('\nINVALID OPTION\n', color=Color.RED, sleep_seconds=2, log_enabled=False)
            _clear()


class UI:
    SPEED = config.UI_SPEED
    TIME = config.DELIVERY_DISPATCH_TIME
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    STRIKETHROUGH = '\u001b[9m'
    ASSIGNED_COLOR = {1: Color.BRIGHT_BLUE, 2: Color.BRIGHT_CYAN, 3: Color.BRIGHT_MAGENTA}
    LOG_FILE = ''

    @staticmethod
    def print(output: str, sleep_seconds: float = 0, color: Color = None, think=False, extra_lines=0,
              log_enabled=True):
        """
        Prints a message to the console.

        Args:
            output (str): The message to print.
            sleep_seconds (float): The number of seconds to sleep after printing the message (default: 0).
            color (Color): The color of the message (default: None).
            think (bool): Indicates if the message should be displayed as if it's thinking (default: False).
            extra_lines (int): The number of extra lines to print after the message (default: 0).
            log_enabled (bool): Indicates if the message should be logged (default: True).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if not config.UI_ELEMENTS_ENABLED:
            color = None
            sleep_seconds = 0
            think = False
        if think:
            output = UI.ITALIC + output + Color.COLOR_ESCAPE.value
        if color:
            output = color.value + output + Color.COLOR_ESCAPE.value
        if config.UI_ENABLED:
            print(output, end='' if think else '\n')
            sleep(sleep_seconds / (config.UI_SPEED / 100))
        if log_enabled:
            UI.LOG_FILE += (output + '\n')
        if think:
            for _ in range(3):
                if config.UI_ENABLED:
                    print((color.value if color else '') + '.' + (Color.COLOR_ESCAPE.value if color else ''),
                          end='', flush=True)
                    sleep(1.5 / (config.UI_SPEED / 100))
            print()
        if extra_lines > 100:
            extra_lines = 100
        for _ in range(extra_lines):
            if log_enabled:
                UI.LOG_FILE += '\n'
            print()

    @staticmethod
    def press_enter_to_continue(simulation_end=False):
        """
        Waits for the user to press the Enter key.

        Args:
            simulation_end (bool): Indicates if simulation should be called afterwords (default: False).

        Time Complexity: O(1)
        Space Complexity: O(1)
        """

        if config.UI_ENABLED and config.UI_ELEMENTS_ENABLED:
            input('\n\nPress Enter key to continue...')
            print('\n\n')
        if simulation_end:
            _simulation()

    @staticmethod
    def menu():
        """
        Displays the main menu and handles user input.

        Time Complexity: O(n log n)
        Space Complexity: O(n)
        """

        UI.print(UI.UNDERLINE + 'Welcome to the WGUPS Parcel Service Terminal' + Color.COLOR_ESCAPE.value,
                 color=Color.BRIGHT_BLUE, sleep_seconds=4, extra_lines=2, log_enabled=False)
        while True:
            UI.print(f'The current time is {UI.TIME}', sleep_seconds=3, extra_lines=2, color=Color.YELLOW
                     , log_enabled=False)
            UI.print(UI.UNDERLINE + 'Please select from the options below' + Color.COLOR_ESCAPE.value,
                     sleep_seconds=2, log_enabled=False)
            UI.print("1. Retrieve current status of today's packages", log_enabled=False)
            UI.print('2. Retrieve package information by ID', log_enabled=False)
            UI.print('3. Time Machine', color=Color.RED, log_enabled=False)
            UI.print('4. View Full "END OF DAY" Log', log_enabled=False)
            UI.print('5. Adjust UI Speed', log_enabled=False)
            UI.print('0. Exit', extra_lines=1, log_enabled=False)
            user_input = input('CHOOSE ONE -> ')
            if not re.match('^[012345]$', user_input.strip()):
                UI.print('\nINVALID OPTION\n', color=Color.RED, sleep_seconds=2, log_enabled=False)
                _clear()
            elif user_input == '1':
                _retrieve_status_of_all_packages()
            elif user_input == '2':
                _retrieve_package_details()
            elif user_input == '3':
                _time_machine()
            elif user_input == '4':
                _view_log()
            elif user_input == '5':
                _adjust_ui_speed()
            else:
                UI.print('\nBYE!', sleep_seconds=2, log_enabled=False)
                break
