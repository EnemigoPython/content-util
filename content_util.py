import json
import sys
import os
from math import floor
from dotenv import load_dotenv
from colorama import Fore, Style, init as colorama_init
from pynput import keyboard
from dataclasses import dataclass, field
from typing import Optional, Callable
import msvcrt

load_dotenv()

QUOTATIONS_PATH = rf"{os.environ.get('quotations_path')}"
STORIES_INDEX_PATH = rf"{os.environ.get('stories_index_path')}"


def clear_stdin():
    while msvcrt.kbhit():
        msvcrt.getch()


def wrap_in_colour(text: str, colour: Optional[Fore]):
    return f"{colour or ''}{text}{Style.RESET_ALL}"


@dataclass
class Option:
    text: str
    colour: Optional[Fore] = None
    screen: Optional['Screen'] = None
    func: Optional[Callable] = None

    def __str__(self) -> str:
        return wrap_in_colour(self.text, self.colour)

@dataclass
class Screen:
    options: list[Option]
    should_exit: bool = False
    current_option: Option = field(init=False)

    def __post_init__(self):
        self.current_option = self.options[0]

    def calculate_whitespace_separator(self, option):
        return floor(round(60 / len(self.options)) - len(str(option)) / 2)

    def print_options(self, flush=True):
        options_display = []
        for option in self.options:
            s = " " * self.calculate_whitespace_separator(option)
            if option is self.current_option:
                curr_colour = self.current_option.colour
                options_display.append(
                    f"{s}{wrap_in_colour('[', curr_colour)} {option} {wrap_in_colour(']', curr_colour)}{s}"
                )
            else:
                options_display.append(f"{s}  {option}  {s}")
        options_line = f'|'.join(options_display)
        print(f"\t{options_line}", end="\r" if flush else None, flush=flush)

    def adjust_current_option(self, pos: int):
        curr_index = self.options.index(self.current_option)
        new_index = (curr_index + pos) % len(self.options)
        self.current_option = self.options[new_index]
        sys.stdout.flush()
        self.print_options()

    def listen(self):
        self.current_option = self.options[0]
        self.print_options()
        listener = keyboard.Listener(on_press=self.handle_input)
        listener.start()
        listener.join()
        if not self.should_exit:
            return self.current_option.screen

    def handle_input(self, key):
        if key == keyboard.Key.esc:
            self.should_exit = True
            return False
        if key == keyboard.Key.enter:
            self.print_options(flush=False)
            if self.current_option.func is not None:
                self.current_option.func()
            return False
        try:
            if key.name == 'left':
                self.adjust_current_option(-1)
            if key.name == 'right':
                self.adjust_current_option(1)
        except AttributeError:
            pass


def view_quotations_func():
    print("\nQuotations:\n")
    with open(QUOTATIONS_PATH, "r") as f:
        quotations = json.load(f)
        for e, q in enumerate(quotations, 1):
            print(f"{e}: {q['text']}\n")
            print(f"Attributed: {q['attributed']}\n")


def main():
    colorama_init()
    quotations = Option(text='quotations', colour=Fore.MAGENTA)
    stories = Option(text='stories', colour=Fore.CYAN)
    _exit = Option(text='exit', colour=Fore.RED)
    screen = Screen([quotations, stories, _exit])

    view_quotations = Option(text='view', colour=Fore.MAGENTA, func=view_quotations_func)
    new_quotation = Option(text='new', colour=Fore.MAGENTA)
    edit_quotation = Option(text='edit', colour=Fore.MAGENTA)
    back_quotations = Option(text='back', colour=Fore.RED)
    quotation_screen = Screen([view_quotations, new_quotation, edit_quotation, back_quotations])
    quotations.screen = quotation_screen
    view_quotations.screen = quotation_screen
    edit_quotation.screen = quotation_screen
    new_quotation.screen = quotation_screen
    back_quotations.screen = screen

    view_stories = Option(text='view', colour=Fore.CYAN)
    new_story = Option(text='new', colour=Fore.CYAN)
    back_stories = Option(text='back', colour=Fore.RED)
    stories_screen = Screen([view_stories, new_story, back_stories])
    stories.screen = stories_screen
    view_stories.screen = stories_screen
    new_story.screen = stories_screen
    back_stories.screen = screen

    print(wrap_in_colour('>', Fore.GREEN))
    while (screen := screen.listen()):
        print(wrap_in_colour('>', screen.current_option.colour))
    print(wrap_in_colour('>', Fore.RED))
    clear_stdin()


if __name__ == '__main__':
    main()
