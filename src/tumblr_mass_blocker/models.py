from dataclasses import asdict
from functools import partial
from typing import Self
from urllib.parse import urlsplit
from webbrowser import open as webbrowser_open

from authlib.integrations.httpx_client import AsyncOAuth1Client
from nicegui import app
from nicegui.binding import bindable_dataclass
from nicegui.ui import button, card, dialog, label
from nicegui.ui import input as ui_input
from pydantic import BaseModel, ConfigDict
from rich.pretty import pprint

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
    client_id: str = ""
    client_secret: str = ""
    token: str = ""
    token_secret: str = ""

    @classmethod
    async def load(cls) -> Self:
        self = cls(**app.storage.general)  # pyright: ignore[reportUnknownArgumentType]

        if not all(asdict(self).values()):
            with dialog().props("persistent").on("hide", lambda: oauth_dialog.clear()) as oauth_dialog, card().classes("w-full"):
                ui_input("OAuth consumer key:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_id")
                ui_input("OAuth consumer secret:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_secret")
                button("Submit tokens", on_click=self.submit_tokens, icon="lock").bind_enabled_from(self, "client_id", lambda client_id: client_id and self.client_secret).bind_enabled_from(self, "client_secret", lambda client_id: client_id and self.client_secret)

                oauth_dialog.open()

            await oauth_dialog

        return self

    async def submit_tokens(self) -> None:
        self.save()

        async with AsyncOAuth1Client(self.client_id, self.client_secret) as client:
            await client.fetch_request_token("https://tumblr.com/oauth/request_token")
            authorization_url = client.create_authorization_url("https://tumblr.com/oauth/authorize")

        label("Press the following button to authorize this application to use your Tumblr.")
        button(authorization_url, on_click=partial(webbrowser_open, authorization_url), icon="open_in_browser")

        ButtonInput(
            "Full Redirected URL",
            partial(self.validate_authorization_response, client),
            partial(self.submit_authorization_response, client),
            "lock",
        )

    @staticmethod
    def validate_authorization_response(client: AsyncOAuth1Client, url: str) -> str | None:
        pprint(client.parse_authorization_response(url))

    async def submit_authorization_response(self, client: AsyncOAuth1Client, url: str) -> None:
        client.parse_authorization_response(url)
        token = await client.fetch_access_token("https://tumblr.com/oauth/access_token")
        await client.aclose()

        self.token = token["oauth_token"]
        self.token_secret = token["oauth_token_secret"]

        self.save()

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
    def validate_url(cls, url: str) -> str | None:
        msg = "Invalid URL"
        try:
            if not cls.from_url(url).blog_name:
                return msg
        except IndexError, ValueError:
            return msg
        return None
