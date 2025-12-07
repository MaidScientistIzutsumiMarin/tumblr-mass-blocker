from random import choice
from sys import exit as sys_exit
from typing import TYPE_CHECKING

from questionary import Choice, checkbox, confirm, select, text
from rich._spinners import SPINNERS
from rich.progress import track
from rich.traceback import install

from tumblr_mass_blocker.console import console
from tumblr_mass_blocker.models import DEFAULT_INT, Post
from tumblr_mass_blocker.tumblr import NotesMode, TumblrClient

if TYPE_CHECKING:
    from collections.abc import Callable


class Main:
    @staticmethod
    def validate_post_url(url: str) -> bool:
        try:
            Post.from_url(url)
        except IndexError:
            return False
        return True

    def __init__(self) -> None:
        action_choices: list[Choice[Callable[[], object]]] = [
            Choice("Set post", self.set_post),
            Choice("Set notes mode", self.set_notes_mode),
            Choice("Preview accounts to block", self.preview_blocks),
            Choice("Quit", sys_exit),
        ]

        with TumblrClient() as self.client:
            while True:
                action = select("Select an action", action_choices).ask()
                action()
                console.clear()
                self.print_info()

    def set_post(self) -> None:
        url = text("Enter the URL of a post:", validate=self.validate_post_url).ask()
        self.post = self.client.retrieve_published_post(url)

    def set_notes_mode(self) -> None:
        mode_choices: list[Choice[NotesMode]] = [
            Choice("All notes", "all"),
            Choice("Only replies and reblogs with added text commentary", "conversation"),
            Choice("Only likes", "likes"),
        ]
        self.notes_mode: NotesMode = checkbox("Select a mode", mode_choices).ask()

    def preview_blocks(self) -> None:
        notes = set(
            track(
                self.client.get_all_notes(
                    self.post,
                    self.notes_mode,
                ),
                total=self.notes_response.total_notes,
            ),
        )
        with console.pager(links=True):
            console.print(*notes, sep="\n")
        console.print("Press [blue]q[/] to quit.", highlight=True)
        if confirm("Block all of these accounts?").ask():
            blog_identifier = text("Enter your blog name:").ask()
            with console.status("Blocking...", spinner=choice(list(SPINNERS))):  # noqa: S311
                self.client.block_a_list_of_blogs(blog_identifier, (note.blog_name for note in notes))
            console.print("[bold green]Done!")

    def print_info(self) -> None:
        console.print(self.post)

        self.notes_response = self.client.get_notes(self.post, None, self.notes_mode)
        if self.notes_response.total_reblogs != DEFAULT_INT:
            console.print(f"Total reblogs: {self.notes_response.total_reblogs}")
        if self.notes_response.total_likes != DEFAULT_INT:
            console.print(f"Total likes: {self.notes_response.total_likes}")
        console.print(f"Total notes: {self.notes_response.total_notes}")


def main() -> None:
    install()

    Main()
