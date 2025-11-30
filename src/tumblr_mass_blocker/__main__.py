from rich import print as rich_print
from rich.console import Console
from rich.traceback import install

from tumblr_mass_blocker.tumblr import TumblrClient


def main() -> None:
    install()

    url = Console().input("Post URL: ")

    with TumblrClient() as client:
        post = client.retrieve_published_post(url)
        rich_print(post)
