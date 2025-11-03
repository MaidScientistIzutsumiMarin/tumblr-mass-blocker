from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from authlib.integrations.httpx_client import AsyncOAuth1Client

if TYPE_CHECKING:
    from httpx import Response


class TumblrSession(AsyncOAuth1Client):
    @staticmethod
    def get_blog_identifier_and_post_id(url: str) -> tuple[str, str]:
        result = urlsplit(url)
        path_parts = result.path.split("/")
        return result.netloc.split(".")[0] if path_parts[1] == "post" else path_parts[1], path_parts[2]

    @classmethod
    def verify_post_url(cls, url: str) -> str | None:
        msg = "Invalid post URL"
        try:
            if not all(cls.get_blog_identifier_and_post_id(url)):
                return msg
        except IndexError:
            return msg

        return None

    def __init__(self) -> None:
        super().__init__(
            # TODO: Read in tokens
            base_url="https://api.tumblr.com/v2/blog",
        )

    async def block_a_list_of_blogs(self, blog_identifier: object, blocked_tumblelogs: list[str]) -> Response:
        return await self.post(
            f"{blog_identifier}/blocks/bulk",
            data={
                "blocked_tumblelogs": blocked_tumblelogs,
            },
        )

    async def retrieve_published_post(self, url: str) -> Response:
        blog_identifier, post_id = self.get_blog_identifier_and_post_id(url)

        return await self.get(
            f"{blog_identifier}/posts",
            params={
                "id": post_id,
                "notes_info": True,
            },
        )
