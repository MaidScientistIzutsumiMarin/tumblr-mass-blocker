from dataclasses import asdict
from functools import cache, partial
from typing import ClassVar, Self
from urllib.parse import urlsplit
from webbrowser import open as webbrowser_open

from authlib.integrations.requests_client import OAuth1Session
from nicegui import app
from nicegui.binding import bindable_dataclass
from nicegui.ui import button, card, dialog, label, separator
from nicegui.ui import input as ui_input
from pydantic import BaseModel, ConfigDict

from tumblr_mass_blocker.helpers import ButtonInput


class FullyValidatedModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
        validate_return=True,
        validate_by_name=True,
    )


@bindable_dataclass
class Tokens:
    session: ClassVar[OAuth1Session | None] = None

    client_id: str = ""
    client_secret: str = ""
    token: str = ""
    token_secret: str = ""

    @classmethod
    @cache
    def get_session(cls, client_id: str, client_secret: str) -> OAuth1Session:
        cls.session = OAuth1Session(client_id, client_secret)
        return cls.session

    @classmethod
    async def load(cls) -> Self:
        self = cls(**app.storage.general)  # pyright: ignore[reportUnknownArgumentType]

        if not all(asdict(self).values()):
            with dialog().props("persistent").on("hide", lambda: cls.oauth_dialog.clear()) as cls.oauth_dialog, card().classes("w-full"):
                ui_input("OAuth consumer key:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_id")
                ui_input("OAuth consumer secret:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_secret")
                button("Submit tokens", on_click=self.submit_tokens, icon="lock").bind_enabled_from(self, "client_id", lambda client_id: client_id and self.client_secret).bind_enabled_from(self, "client_secret", lambda client_secret: client_secret and self.client_id)

                cls.oauth_dialog.open()

            await cls.oauth_dialog

        return self

    def submit_tokens(self) -> None:
        self.save()

        session = self.get_session(self.client_id, self.client_secret)
        session.fetch_request_token("https://tumblr.com/oauth/request_token")
        authorization_url = session.create_authorization_url("https://tumblr.com/oauth/authorize")

        separator()
        label("Press the button below to open a browser window and authorize this application.")
        button("Authorize application", on_click=partial(webbrowser_open, authorization_url), icon="open_in_browser")
        ButtonInput(
            "Full Redirected URL",
            self.submit_authorization_response,
            "lock",
            lambda url: "oauth_verifier" not in session.parse_authorization_response(url),
        )

    async def submit_authorization_response(self, url: str) -> None:
        session = self.get_session(self.client_id, self.client_secret)
        session.parse_authorization_response(url)
        token = session.fetch_access_token("https://tumblr.com/oauth/access_token")

        self.token = token["oauth_token"]
        self.token_secret = token["oauth_token_secret"]

        self.save()

        label("Authentication successful!").classes("text-positive")
        button("Close", on_click=self.oauth_dialog.close)

    def save(self) -> None:
        app.storage.general.update(asdict(self))


class ResponseModel(FullyValidatedModel):
    response: Response


class Response(FullyValidatedModel):
    posts: list[Post]


class Post(FullyValidatedModel):
    blog_name: str
    id: int

    tags: list[str] = []
    body: str = ""

    @classmethod
    def from_url(cls, url: str) -> Self:
        result = urlsplit(url)
        path_parts = result.path.split("/")
        return cls(
            blog_name=result.netloc.split(".")[0] if path_parts[1] == "post" else path_parts[1],
            id=int(path_parts[2]),
        )

    @classmethod
    def validate_url(cls, url: str) -> bool:
        return not cls.from_url(url).blog_name
