from typing import ClassVar

from httpx import HTTPStatusError
from nicegui import app
from nicegui.ui import card, expansion, html, label, refreshable_method, row, run  # pyright: ignore[reportUnknownVariableType]
from winloop import new_event_loop

from tumblr_mass_blocker.helpers import ButtonInput
from tumblr_mass_blocker.models import Post, Tokens
from tumblr_mass_blocker.tumblr import TumblrClient


class Root:
    client: ClassVar[TumblrClient | None] = None

    @classmethod
    async def get_client(cls) -> TumblrClient:
        if cls.client is None:
            tokens = await Tokens.load()
            cls.client = TumblrClient(tokens)
        return cls.client

    async def setup(self) -> None:
        ButtonInput("Post URL", self.render_post.refresh, "search", Post.validate_url)

        with expansion("Post Preview").classes("w-full"), card().classes("w-full"):
            await self.render_post("")

    @refreshable_method
    async def render_post(self, url: str) -> None:
        if not url:
            return

        client = await self.get_client()
        try:
            post = await client.retrieve_published_post(url)
        except HTTPStatusError as error:
            label("Unable to load post!").classes("text-negative")
            label(str(error)).classes("text-bold text-negative")
        else:
            html(post.body, sanitize=False)
            with row():
                for tag in post.tags:
                    label(f"#{tag}").classes("text-grey")


async def on_shutdown() -> None:
    if Root.client is not None:
        await Root.client.aclose()
    if Tokens.session is not None:
        Tokens.session.close()


def main() -> None:
    app.on_shutdown(on_shutdown)  # pyright: ignore[reportUnknownMemberType]
    run(
        Root().setup,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
        loop=new_event_loop,
    )
