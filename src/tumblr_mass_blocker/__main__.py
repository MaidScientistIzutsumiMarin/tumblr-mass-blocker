from httpx import HTTPStatusError
from nicegui import app
from nicegui.ui import button, card, expansion, html, label, refreshable_method, row, run, space  # pyright: ignore[reportUnknownVariableType]

from tumblr_mass_blocker.helpers import ButtonInput
from tumblr_mass_blocker.models import Post, Tokens
from tumblr_mass_blocker.tumblr import TumblrSession


class Root:
    async def setup(self) -> None:
        ButtonInput("Post URL", Post.validate_url, self.render_post.refresh, "search")

        with expansion("Post Preview").classes("w-full"), card().classes("w-full"):
            await self.render_post("")

        with row(align_items="center").classes("w-full"):
            space()
            button("Quit", on_click=app.shutdown)

        self.session = None

    @refreshable_method
    async def render_post(self, url: str) -> None:
        if not url:
            return

        if self.session is None:
            tokens = await Tokens.load()
            self.session = TumblrSession(tokens)

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
    root = Root()
    app.on_shutdown(lambda: root.session is not None and root.session.aclose())  # pyright: ignore[reportUnknownMemberType]
    run(
        root.setup,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
    )
