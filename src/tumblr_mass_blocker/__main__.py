from dataclasses import dataclass
from typing import ClassVar, Literal, cast, get_args

from rich import print as rich_print
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.prompt import Confirm
from rich.traceback import install
from rich_menu import Menu

from tumblr_mass_blocker.models import DEFAULT_INT, Note, Post
from tumblr_mass_blocker.tumblr import ModeType, TumblrClient

ActionType = Literal["Set post", "Set notes mode", "Preview accounts to block"]


class Main:
    options_to_modes: ClassVar[dict[str, ModeType]] = {
        "All notes": "all",
        "Only replies and reblogs with added text commentary": "conversation",
        "Only likes": "likes",
    }

    def __post_init__(self) -> None:
        selected: str = next(iter(self.options_to_modes))
        with TumblrClient() as self.client:
            while True:
                run = False
                match cast("ActionType", Menu(*get_args(ActionType)).ask(screen=False)):
                    case "Set post":
                        url = Console().input("Post URL: ")
                        self.post = self.client.retrieve_published_post(url)
                    case "Set notes mode":
                        self.selected = Menu(*self.options_to_modes).ask(screen=False)
                        self.notes_response = self.client.get_notes(self.post, None, self.options_to_modes[self.selected])
                    case _:
                        if post is not None:
                            notes = self.print_notes()
                            if Confirm.ask("Block all of these accounts?"):
                                for _ in track(notes):
                                    ...
                Console().clear()

                if post is not None:
                    rich_print(post)
                    self.print_note_totals()

    def print_note_totals(self) -> None:
        self.total_notes = response.total_notes
        if response.total_reblogs != DEFAULT_INT:
            rich_print(f"Total reblogs: {response.total_reblogs}")
        if response.total_likes != DEFAULT_INT:
            rich_print(f"Total likes: {response.total_likes}")
        rich_print(f"Total notes: {self.total_notes}")

    def print_notes(self) -> set[Note]:
        columns = Columns(expand=True, equal=True)
        notes = set[Note]()
        if self.post is None:
            return notes

        for note in track(self.client.get_all_notes(self.post, self.options_to_modes[self.selected]), total=self.total_notes):
            if note not in notes:
                columns.add_renderable(note)
                notes.add(note)
        rich_print(Panel(columns))
        return notes


def main() -> None:
    install()

    Main()
