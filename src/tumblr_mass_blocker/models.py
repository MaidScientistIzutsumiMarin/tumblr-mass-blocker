from dataclasses import asdict, dataclass
from json import dumps, loads
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Self
from urllib.parse import urlsplit

from authlib.integrations.httpx_client import OAuth1Client
from pydantic import BaseModel, ConfigDict, Field
from questionary import password
from rich.panel import Panel

from tumblr_mass_blocker import __version__
from tumblr_mass_blocker.console import console

if TYPE_CHECKING:
    from collections.abc import Generator

DEFAULT_INT = -1


@dataclass
class Tokens:
    path: ClassVar = Path("tokens.json")
    client_id: str = ""
    client_secret: str = ""
    token: str = ""
    token_secret: str = ""

    @staticmethod
    def online_token_prompt(url: str, *tokens: str) -> Generator[str]:
        formatted_token_string = " and ".join(f"[cyan]{token}[/]" for token in tokens)

        console.print(f"Retrieve your {formatted_token_string} from: {url}")
        for token in tokens:
            yield password(f"Enter your {token} (masked):").ask()

        console.print()

    def __post_init__(self) -> None:
        if self.path.exists():
            for name, value in loads(self.path.read_text()).items():
                setattr(self, name, value)

        if not all(asdict(self).values()):
            if not self.client_id or not self.client_secret:
                self.client_id, self.client_secret = self.online_token_prompt("https://tumblr.com/oauth/apps", "consumer key", "consumer secret")
                self.save()

            with OAuth1Client(
                self.client_id,
                self.client_secret,
                headers={"user-agent": f"tumblr-mass-blocker/{__version__}"},  # The HTTPX user-agent is blocked...
                http2=True,
                base_url="https://www.tumblr.com/oauth",
            ) as client:
                client.fetch_request_token("request_token")  # pyright: ignore[reportUnknownMemberType]

                authorization_url = client.create_authorization_url("https://tumblr.com/oauth/authorize")
                console.print("Open the link below in your browser, and authorize this application.\nAfter authorizing, copy and paste the URL of the page you are redirected to below.")
                (authorization_response,) = self.online_token_prompt(authorization_url, "full redirect URL")
                client.parse_authorization_response(authorization_response)

                token = client.fetch_access_token("access_token")

            self.token = token["oauth_token"]
            self.token_secret = token["oauth_token_secret"]

            self.save()

    def save(self) -> None:
        self.path.write_text(dumps(asdict(self)))


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
                before_timestamp: int = DEFAULT_INT

            query_params: QueryParams = QueryParams()

        next: Next = Next()

    notes: list[Note]
    total_notes: int
    total_likes: int = DEFAULT_INT
    total_reblogs: int = DEFAULT_INT
    links: Links = Field(default_factory=Links, validation_alias="_links")


class Post(FullyValidatedModel):
    class Block(FullyValidatedModel):
        type: str
        text: str = ""

    blog_name: str
    id: int

    tags: list[str] = []
    content: list[Block] = []

    @classmethod
    def from_url(cls, url: str) -> Self:
        result = urlsplit(url)
        path_parts = result.path.split("/")
        return cls(
            blog_name=result.netloc.split(".")[0] if path_parts[1] == "post" else path_parts[1],
            id=int(path_parts[2]),
        )

    def __rich__(self) -> Panel:
        return Panel(
            "\n\n".join(block.text for block in self.content).strip(),
            title=self.blog_name,
            subtitle=" ".join(f"#{tag}" for tag in self.tags),
            subtitle_align="left",
            expand=False,
        )


class Note(FullyValidatedModel):
    model_config = ConfigDict(frozen=True)

    blog_name: str
    blog_url: str

    def __rich__(self) -> str:
        return f"[link={self.blog_url}]{self.blog_name}[/link]"
