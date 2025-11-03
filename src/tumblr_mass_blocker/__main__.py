from nicegui import app
from nicegui.binding import bindable_dataclass
from nicegui.ui import button, row, run, space  # pyright: ignore[reportUnknownVariableType]
from niquests import AsyncSession


@bindable_dataclass
class Root:
    session: AsyncSession
    enabled = True

    async def setup(self) -> None:
        with row(align_items="center").classes("w-full"):
            space()
            button("Quit", on_click=app.shutdown).bind_enabled_from(self)


def main() -> None:
    run(
        start,
        title="Tumblr Mass Blocker",
        dark=None,
        native=True,
        reload=False,
    )


async def start() -> None:
    async with AsyncSession() as session:
        await Root(session).setup()
