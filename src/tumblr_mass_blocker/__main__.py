from random import choice
from typing import Literal, get_args

from questionary import confirm, select, text
from rich._spinners import SPINNERS
from rich.console import Console
from rich.progress import track
from rich.traceback import install

from tumblr_mass_blocker.models import DEFAULT_INT, Post
from tumblr_mass_blocker.tumblr import ModeType, TumblrClient

ActionType = Literal["Set post", "Set notes mode", "Preview accounts to block", "Quit"]


def main() -> None:
    install()

    mode_choices: list[dict[str, ModeType]] = [
        {"All notes": "all", "Only replies and reblogs with added text commentary": "conversation", "Only likes": "likes"},
    ]
    console = Console()

    post = None
    notes_mode = next(iter(mode_choices[0].values()))
    notes_response = None

    with TumblrClient() as client:
        while True:
            selection: ActionType = select("Select an action", get_args(ActionType)).ask()
            match selection:
                case "Set post":
                    url: str = text("Enter the URL of a post:", validate=validate_post_url).ask()
                    post = client.retrieve_published_post(url)
                case "Set notes mode":
                    notes_mode: ModeType = select("Select a mode", mode_choices).ask()
                    if post is not None:
                        notes_response = client.get_notes(post, None, notes_mode)
                case "Preview accounts to block":
                    if post is not None and notes_response is not None:
                        notes = set(track(client.get_all_notes(post, notes_mode), total=notes_response.total_notes))
                        console.print("Press [blue]q[/] to quit.")
                        with console.pager(links=True):
                            console.print(*notes, sep="\n")
                        if confirm("Block all of these accounts?").ask():
                            blog_identifier: str = text("Enter your blog name:").ask()
                            with console.status("Blocking...", spinner=choice(list(SPINNERS))):  # noqa: S311
                                client.block_a_list_of_blogs(blog_identifier, (note.blog_name for note in notes))
                            console.print("[bold green]Done!")
                case _:
                    break

            console.clear()

            if post is not None:
                console.print(post)
                notes_response = client.get_notes(post, None, notes_mode)
                if notes_response.total_reblogs != DEFAULT_INT:
                    console.print(f"Total reblogs: {notes_response.total_reblogs}")
                if notes_response.total_likes != DEFAULT_INT:
                    console.print(f"Total likes: {notes_response.total_likes}")
                console.print(f"Total notes: {notes_response.total_notes}")


def validate_post_url(url: str) -> bool:
    try:
        Post.from_url(url)
    except IndexError:
        return False
    return True
