from functools import partial
from operator import is_
from typing import ClassVar

from httpx import HTTPStatusError
from nicegui import app
from nicegui.ui import button, card, expansion, html, label, refreshable_method, row, run, space  # pyright: ignore[reportUnknownVariableType]

from tumblr_mass_blocker.helpers import BindableInput
from tumblr_mass_blocker.models import Post
from tumblr_mass_blocker.tumblr import TumblrSession


class Root:
    session: ClassVar = TumblrSession()

    async def setup(self) -> None:
        with row(wrap=False, align_items="center").classes("w-full"):
            url_input = BindableInput("Post URL", validation=Post.validate_url).classes("w-full").props("clearable").on("keydown.enter", lambda: process_url_button.enabled and process_url_button.run_method("click"))
            process_url_button = button(on_click=lambda: self.render_post.refresh(url_input.value), icon="send").bind_enabled_from(url_input, "_error", backward=partial(is_, None))

            url_input.error = ""

        with expansion("Post Preview").classes("w-full"), card().classes("w-full"):
            await self.render_post("")

        with row(align_items="center").classes("w-full"):
            space()
            button("Quit", on_click=app.shutdown)

    @refreshable_method
    async def render_post(self, url: str) -> None:
        if not url:
            return

        try:
            post = await self.session.retrieve_published_post(url)
            html(post.body, sanitize=False)
            with row():
                for tag in post.tags:
                    label(f"#{tag}").classes("text-grey")
        except HTTPStatusError as error:
            label("Unable to load post!").classes("text-negative")
            label(str(error)).classes("text-bold text-negative")


def main() -> None:
    app.on_shutdown(Root.session.aclose)  # pyright: ignore[reportUnknownMemberType]

    run(
        Root().setup,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
    )
