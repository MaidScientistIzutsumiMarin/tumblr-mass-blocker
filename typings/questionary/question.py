from questionary.constants import DEFAULT_KBI_MESSAGE


class Question[T]:
    def ask(
        self,
        *,
        patch_stdout: bool = False,
        kbi_msg: str = DEFAULT_KBI_MESSAGE,
    ) -> T: ...
