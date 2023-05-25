from time import sleep

from src import config
from src.constants.color import Color


class UI:

    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    ASSIGNED_COLOR = {1: Color.BRIGHT_BLUE, 2: Color.BRIGHT_CYAN, 3: Color.BRIGHT_MAGENTA}

    @staticmethod
    def print(output: str, sleep_seconds: float = 0, color: Color = None, think=False, extra_lines=0):
        if config.UI_ENABLED:
            if not config.UI_ELEMENTS_ENABLED:
                color = None
                sleep_seconds = 0
                think = False
            if think:
                output = UI.ITALIC + output + Color.COLOR_ESCAPE.value[0]
            if color:
                output = color.value[0] + output + Color.COLOR_ESCAPE.value[0]
            print(output, end='' if think else '\n')
            sleep(sleep_seconds / (config.UI_SPEED / 100))
            if think:
                for _ in range(3):
                    print((color.value[0] if color else '') + '.' + (Color.COLOR_ESCAPE.value[0] if color else ''),
                          end='', flush=True)
                    sleep(1.5 / (config.UI_SPEED / 100))
                print()
            for _ in range(extra_lines):
                print()

    @staticmethod
    def press_enter_to_continue():
        if config.UI_ENABLED and config.UI_ELEMENTS_ENABLED:
            input('\n\nPress Enter key to continue...')
            print('\n\n')
