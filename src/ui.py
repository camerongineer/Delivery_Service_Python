import msvcrt
import os
from time import sleep

from src import config
from src.constants.color import Color


class UI:

    @staticmethod
    def print(output: str, sleep_seconds: float = 0, color: Color = None, think=False, extra_lines=0):
        if color:
            output = color.value[0] + output
        print(output, end='' if think else '\n')
        sleep(sleep_seconds / (config.UI_SPEED / 100))
        if think:
            for _ in range(8):
                print((color.value[0] if color else '') + '.', end='', flush=True)
                sleep(.5 / (config.UI_SPEED / 100))
            print()
        for _ in range(extra_lines):
            print()

    @staticmethod
    def press_enter_to_continue():
        print('Press Enter key to continue...\n\n')
        input()
        os.system('cls' if os.name == 'nt' else 'clear')

