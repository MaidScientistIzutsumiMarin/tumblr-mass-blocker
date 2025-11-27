from dataclasses import asdict
from typing import TYPE_CHECKING, Literal

from authlib.integrations.httpx_client import OAuth1Auth
from httpx import AsyncClient, Response

from tumblr_mass_blocker.models import Note, NoteResponse, Post, PostResponse, ResponseModel, Tokens

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

ModeType = Literal["all", "likes", "conversation", "rollup", "rollup_with_tags"]


class TumblrClient(AsyncClient):
    @staticmethod
    async def raise_for_status(response: Response) -> None:
        response.raise_for_status()

    def __init__(self, tokens: Tokens) -> None:
        super().__init__(
            auth=OAuth1Auth(**asdict(tokens)),
            http2=True,
            event_hooks={"response": [self.raise_for_status]},
            base_url="https://api.tumblr.com/v2/blog",
        )

    async def block_a_list_of_blogs(self, blog_identifier: str, blocked_tumblelogs: list[str]) -> None:
        await self.post(
            f"{blog_identifier}/blocks/bulk",
            data={
                "blocked_tumblelogs": blocked_tumblelogs,
            },
        )

    async def retrieve_published_post(self, url: str) -> Post:
        post = Post.from_url(url)

        response = await self.get(
            f"{post.blog_name}/posts",
            params={
                "id": post.id,
            },
        )
        return ResponseModel[PostResponse].model_validate_json(response.text).response.posts[0]

    async def get_notes(self, post: Post, before_timestamp: int | None, mode: ModeType) -> NoteResponse:
        response = await self.get(
            f"{post.blog_name}/notes",
            params={
                "id": post.id,
                "before_timestamp": before_timestamp,
                "mode": mode,
            },
        )
        return ResponseModel[NoteResponse].model_validate_json(response.text).response

    async def get_all_notes(self, post: Post, mode: ModeType) -> AsyncGenerator[Note]:
        before_timestamp = None
        while True:
            response = await self.get_notes(post, before_timestamp, mode)
            for note in response.notes:
                yield note
            if response.links is None:
                break
            before_timestamp = response.links.next.query_params.before_timestamp
