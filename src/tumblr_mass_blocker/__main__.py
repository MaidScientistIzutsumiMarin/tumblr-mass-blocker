from dataclasses import dataclass, field
from random import choice
from sys import exit as sys_exit
from typing import TYPE_CHECKING

from questionary import Choice, confirm, press_any_key_to_continue, select, text
from rich._spinners import SPINNERS
from rich.progress import track
from rich.traceback import install

from tumblr_mass_blocker.console import console
from tumblr_mass_blocker.models import NoteResponse, Post
from tumblr_mass_blocker.tumblr import NotesMode, TumblrClient

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class Main:
    client: TumblrClient = field(default_factory=TumblrClient)
    notes_mode: NotesMode = "all"
    post: Post | None = None
    notes_response: NoteResponse | None = None

    @staticmethod
    def validate_post_url(url: str) -> bool:
        try:
            Post.from_url(url)
        except IndexError:
            return False
        return True

    def __post_init__(self) -> None:
        action_choices: list[Choice[Callable[[], object]]] = [
            Choice("Set post", self.set_post, description="Set the post to load notes from."),
            Choice("Set notes mode", self.set_notes_mode, description="Select one of several modes to filter notes by."),
            Choice("Preview accounts to block", self.preview_blocks, description="Display all of the accounts that will be blocked with the current settings then prompt for confirmation to block."),
            Choice("Quit", sys_exit, description="Quit this program."),
        ]

        with self.client:
            while True:
                console.rule()
                action = select("Select an action", action_choices).ask()
                action()
                console.clear()
                console.rule()
                self.print_info()

    def set_post(self) -> None:
        url = text("Enter the URL of a post:", validate=self.validate_post_url).ask()
        self.post = self.client.retrieve_published_post(url)

    def set_notes_mode(self) -> None:
        mode_choices: list[Choice[NotesMode]] = [
            Choice("All", "all", description="Load all notes."),
            Choice("Added text commentary", "conversation", description="Load only replies and reblogs with added text commentary, excluding the rest of the notes (likes, reblogs without commentary)."),
            Choice("Likes", "likes", description="Load only likes, excluding the rest of the notes (replies, reblogs)."),
        ]
        self.notes_mode = select("Select a mode", mode_choices).ask()

    def preview_blocks(self) -> None:
        if self.post is None or self.notes_response is None:
            return

        notes = set(
            track(
                self.client.get_all_notes(
                    self.post,
                    self.notes_mode,
                ),
                total=self.notes_response.total_notes,
            ),
        )

        with console.pager(styles=True, links=True):
            console.print("[Press [blue]q[/] to quit.]", style="bold")
            console.print(*sorted(notes), sep="\n")
        if confirm("Block all of these accounts?", default=False).ask():
            blog_identifier = text("Enter your blog name:", validate=bool).ask()
            if confirm("Are you sure? This is not (easily) reversible.", default=False).ask():
                with console.status("Blocking...", spinner=choice(list(SPINNERS))):  # noqa: S311
                    self.client.block_a_list_of_blogs(blog_identifier, (note.blog_name for note in notes))
                console.print("Done!", style="bold green")
                press_any_key_to_continue().ask()

    def print_info(self) -> None:
        if self.post is None:
            return

        self.notes_response = self.client.get_notes(self.post, None, self.notes_mode)
        console.print(f"Total notes: {self.notes_response.total_notes}", style="italic")

        console.print(self.post)


def main() -> None:
    install()

    Main()
