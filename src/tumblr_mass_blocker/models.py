from typing import Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict


class FullyValidatedModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        validate_default=True,
        validate_return=True,
        validate_by_name=True,
    )


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
