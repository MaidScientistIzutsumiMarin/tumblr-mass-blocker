from nicegui.binding import BindableProperty
from nicegui.ui import input as ui_input


# This is a slightly hacky way to make nearly any attribute of any class bindable.
# Bindable properties are far more efficient than active links, which is the alternative.
class BindableInput(ui_input):
    _error = BindableProperty()  # pyright: ignore[reportAssignmentType]
