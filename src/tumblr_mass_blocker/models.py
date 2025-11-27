from dataclasses import asdict
from functools import partial
from typing import Literal, Self
from urllib.parse import urlsplit
from webbrowser import open as webbrowser_open

from authlib.integrations.httpx_client import AsyncOAuth1Client
from nicegui import app
from nicegui.binding import bindable_dataclass
from nicegui.ui import button, card, dialog, html, label, row, separator, spinner
from nicegui.ui import input as ui_input
from pydantic import BaseModel, ConfigDict, Field

from tumblr_mass_blocker import __version__
from tumblr_mass_blocker.utils import ButtonInput

type NoteType = Literal["posted", "reply", "reblog", "like"]


@bindable_dataclass
class Tokens:
    client_id: str = ""
    client_secret: str = ""
    token: str = ""
    token_secret: str = ""

    async def __aenter__(self) -> Self:
        if not all(asdict(self).values()):
            with dialog().props("persistent").on("hide", lambda: self.oauth_dialog.clear()) as self.oauth_dialog, card().classes("w-full"):
                label("Enter your OAuth consumer key and secret from the Tumblr Applications dashboard.")
                ui_input("OAuth consumer key:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_id")
                ui_input("OAuth consumer secret:", password=True, password_toggle_button=True).classes("w-full").bind_value(self, "client_secret")

                with row():
                    button("Submit tokens", on_click=self.submit_tokens, icon="key").bind_enabled_from(self, "client_id", lambda client_id: client_id and self.client_secret).bind_enabled_from(self, "client_secret", lambda client_secret: client_secret and self.client_id)
                    button("Tumblr Applications", on_click=partial(webbrowser_open, "tumblr.com/oauth/apps"), icon="open_in_browser")

                self.oauth_dialog.open()

            await self.oauth_dialog

        return self

    async def __aexit__(self, *_: object) -> None:
        if hasattr(self, "client"):
            await self.client.aclose()

    async def submit_tokens(self) -> None:
        self.save()

        self.client = AsyncOAuth1Client(
            self.client_id,
            self.client_secret,
            headers={"user-agent": f"tumblr-mass-blocker/{__version__}"},  # The HTTPX user-agent is blocked...
            http2=True,
            base_url="https://www.tumblr.com/oauth",
        )
        await self.client.fetch_request_token("request_token")
        authorization_url = self.client.create_authorization_url("https://tumblr.com/oauth/authorize")

        separator()
        label("Press the button below to open a browser window, and authorize this application.")
        button("Authorize application", on_click=partial(webbrowser_open, authorization_url), icon="open_in_browser")
        label("After authorizing, copy and paste the URL of the page you are redirected to below.")
        ButtonInput(
            "Full Redirected URL",
            self.submit_authorization_response,
            "login",
            lambda url: "oauth_verifier" not in self.client.parse_authorization_response(url),
        )

    async def submit_authorization_response(self, url: str) -> None:
        authorize_spinner = spinner(size="1.5em")

        self.client.parse_authorization_response(url)
        token = await self.client.fetch_access_token("access_token")

        self.token = token["oauth_token"]
        self.token_secret = token["oauth_token_secret"]

        self.save()

        authorize_spinner.set_visibility(False)
        label("Authentication successful!").classes("text-positive")
        button("Close", on_click=self.oauth_dialog.close)

    def save(self) -> None:
        app.storage.general.update(asdict(self))


class FullyValidatedModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
        validate_return=True,
        validate_by_name=True,
    )


class ResponseModel[T](FullyValidatedModel):
    response: T


class PostResponse(FullyValidatedModel):
    posts: list[Post]


class NoteResponse(FullyValidatedModel):
    class Links(FullyValidatedModel):
        class Next(FullyValidatedModel):
            class QueryParams(FullyValidatedModel):
                before_timestamp: int

            query_params: QueryParams

        next: Next

    notes: list[Note]
    total_notes: int
    total_likes: int = -1
    total_reblogs: int = -1
    links: Links | None = Field(validation_alias="_links")


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

    def render(self) -> None:
        html(self.body, sanitize=False)
        with row():
            for tag in self.tags:
                label(f"#{tag}").classes("text-grey")


class Note(FullyValidatedModel):
    blog_name: str
