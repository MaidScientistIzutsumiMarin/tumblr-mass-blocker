from functools import partial
from operator import is_
from typing import TYPE_CHECKING

from nicegui.binding import BindableProperty
from nicegui.ui import button, row
from nicegui.ui import input as ui_input

if TYPE_CHECKING:
    from collections.abc import Callable

    from nicegui.elements.mixins.validation_element import ValidationDict, ValidationFunction


# This is a slightly hacky way to make nearly any attribute of any class bindable.
# Bindable properties are far more efficient than active links, which is the alternative.
class ButtonInput(ui_input):
    _error = BindableProperty()  # pyright: ignore[reportAssignmentType]

    def __init__(
        self,
        label: str,
        validation: ValidationFunction | ValidationDict,
        on_click: Callable[[str], object],
        icon: str,
    ) -> None:
        with row(wrap=False, align_items="center").classes("w-full"):
            super().__init__(label, validation=validation)

            self.classes("w-full").props("clearable").on("keydown.enter", lambda: submit_button.enabled and submit_button.run_method("click"))
            submit_button = button(on_click=lambda: on_click(self.value), icon=icon).bind_enabled_from(self, "_error", partial(is_, None))

        self.error = ""
