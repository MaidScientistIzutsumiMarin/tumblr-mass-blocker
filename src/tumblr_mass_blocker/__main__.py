from typing import ClassVar

from nicegui import app
from nicegui.binding import bindable_dataclass
from nicegui.ui import button, card, expansion, html, label, refreshable_method, row, space
from nicegui.ui import input as ui_input
from nicegui.ui import run as ui_run  # pyright: ignore[reportUnknownVariableType]

from tumblr_mass_blocker.tumblr import TumblrSession


@bindable_dataclass
class Root:
    session: ClassVar = TumblrSession()
    enabled = True

    @classmethod
    async def shutdown(cls) -> None:
        app.shutdown()
        await cls.session.aclose()

    async def setup(self) -> None:
        with ui_input("Post URL", validation=self.session.verify_post_url).classes("w-full").props("clearable").bind_enabled_from(self) as url_input:
            button(on_click=lambda: self.render_post.refresh(url_input.value), icon="send")

        with expansion("Post Preview").classes("w-full"), card().classes("w-full"):
            await self.render_post("")

        with row(align_items="center").classes("w-full"):
            space()
            button("Quit", on_click=self.shutdown).bind_enabled_from(self)

    @refreshable_method
    async def render_post(self, url: str) -> None:
        if not url:
            return

        response = await self.session.retrieve_published_post(url)
        post = response.json()["response"]["posts"][0]
        html(post["body"], sanitize=False)
        label("#" + " #".join(post["tags"])).classes("text-grey")


def main() -> None:
    ui_run(
        Root().setup,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
    )
