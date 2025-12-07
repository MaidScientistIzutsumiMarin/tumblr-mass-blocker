from typing import TYPE_CHECKING

from questionary.constants import DEFAULT_QUESTION_PREFIX, DEFAULT_SELECTED_POINTER

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from prompt_toolkit.styles import Style

    from questionary.prompts.common import Choice
    from questionary.question import Question


def checkbox[T](  # noqa: PLR0913
    message: str,
    choices: Sequence[str | Choice[T] | dict[str, object]],
    default: str | None = None,
    validate: Callable[[list[str]], bool | str] = lambda _a: True,
    qmark: str = DEFAULT_QUESTION_PREFIX,
    pointer: str | None = DEFAULT_SELECTED_POINTER,
    style: Style | None = None,
    initial_choice: str | Choice[T] | dict[str, object] | None = None,
    *,
    use_arrow_keys: bool = True,
    use_jk_keys: bool = True,
    use_emacs_keys: bool = True,
    use_search_filter: str | bool | None = False,
    instruction: str | None = None,
    show_description: bool = True,
    **kwargs: object,
) -> Question[T]: ...
