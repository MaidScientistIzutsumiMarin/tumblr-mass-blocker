from nicegui.binding import BindableProperty
from nicegui.ui import input as ui_input


class BindableInput(ui_input):
    _error = BindableProperty()  # pyright: ignore[reportAssignmentType]
