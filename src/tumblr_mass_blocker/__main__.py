from typing import ClassVar

from httpx import HTTPStatusError
from nicegui import app
from nicegui.events import ValueChangeEventArguments  # noqa: TC002
from nicegui.ui import button, card, expansion, label, notify, refreshable_method, row, run, select  # pyright: ignore[reportUnknownVariableType]
from winloop import new_event_loop

from tumblr_mass_blocker.models import Post, Tokens
from tumblr_mass_blocker.tumblr import ModeType, TumblrClient
from tumblr_mass_blocker.utils import ButtonInput


class Root:
    names_to_modes: ClassVar[dict[str, ModeType]] = {
        "All notes": "all",
        "Only likes": "likes",
        "Only replies and reblogs with added text commentary": "conversation",
    }

    @classmethod
    async def create(cls) -> None:
        self = cls()
        ButtonInput("Post URL", self.load_post.refresh, "search", lambda url: not Post.from_url(url).blog_name)
        await self.load_post("")

    @refreshable_method
    async def load_post(self, url: str) -> None:
        if not url:
            return

        if not hasattr(self, "client"):
            async with Tokens(**app.storage.general) as tokens:  # pyright: ignore[reportUnknownArgumentType]
                self.client = TumblrClient(tokens)

        try:
            self.post = await self.client.retrieve_published_post(url)
        except HTTPStatusError as error:
            notify(f"Unable to load post!\n{error}", type="negative", multi_line=True)
        else:
            with expansion("Post Preview").classes("w-full"), card().classes("w-full"):
                self.post.render()

            label("Select what categories of notes to block from:")
            with row(wrap=False, align_items="center").classes("w-full"):
                select(
                    list(self.names_to_modes),
                    label="Mode",
                    on_change=lambda args: self.select_mode.refresh(args),
                ).classes("w-full").set_value(next(iter(self.names_to_modes)))
                button("Block Accounts")

            with card():
                await self.select_mode(None)

    @refreshable_method
    async def select_mode(self, args: ValueChangeEventArguments | None) -> None:
        if args is None:
            return
        notes = await self.client.get_notes(self.post, None, self.names_to_modes[args.value])
        if notes.total_reblogs != -1:
            label(f"Reblog Count: {notes.total_reblogs}")
        if notes.total_likes != -1:
            label(f"Like Count: {notes.total_likes}")
        label(f"Total Note Count: {notes.total_notes}")


def main() -> None:
    run(
        Root.create,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
        loop=new_event_loop,
    )
