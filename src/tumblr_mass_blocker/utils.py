from functools import partial
from operator import is_
from typing import TYPE_CHECKING

from nicegui.binding import BindableProperty
from nicegui.functions import clipboard
from nicegui.ui import button, row
from nicegui.ui import input as ui_input

if TYPE_CHECKING:
    from collections.abc import Callable


# This is a slightly hacky way to make nearly any attribute of any class bindable.
# Bindable properties are far more efficient than active links, which is the alternative.
class ButtonInput(ui_input):
    _error = BindableProperty()  # pyright: ignore[reportAssignmentType]

    def __init__(
        self,
        label: str,
        on_click: Callable[[str], object],
        icon: str,
        validation: Callable[[str], bool],
    ) -> None:
        with row(wrap=False, align_items="center").classes("w-full"):
            super().__init__(label, validation=self.try_validation)

            self.classes("w-full").props("clearable").on("keydown.enter", lambda: submit_button.enabled and submit_button.run_method("click"))
            button(on_click=self.paste_clipboard, icon="content_paste")
            submit_button = button(on_click=lambda: on_click(self.value), icon=icon).bind_enabled_from(self, "_error", partial(is_, None))

        self.error = ""
        self.inner_validation = validation

    def try_validation(self, url: str) -> str | None:
        msg = "Invalid input"
        try:
            if self.inner_validation(url):
                return msg
        except Exception:  # noqa: BLE001
            return msg

    async def paste_clipboard(self) -> None:
        value = await clipboard.read()
        self.set_value(value)
