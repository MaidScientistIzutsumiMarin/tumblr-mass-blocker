from dataclasses import asdict
from typing import TYPE_CHECKING, Literal

from authlib.integrations.httpx_client.oauth1_client import OAuth1Auth
from httpx import Client, Response

from tumblr_mass_blocker.models import DEFAULT_INT, Note, NoteResponse, Post, PostResponse, ResponseModel, Tokens

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

type NotesMode = Literal["all", "likes", "conversation", "rollup", "rollup_with_tags"]


class TumblrClient(Client):
    def __init__(self) -> None:
        super().__init__(
            auth=OAuth1Auth(**asdict(Tokens())),
            http2=True,
            event_hooks={"response": [Response.raise_for_status]},
            base_url="https://api.tumblr.com/v2/blog",
        )

    def block_a_list_of_blogs(self, blog_identifier: str, blocked_tumblelogs: Iterable[str]) -> None:
        self.post(
            f"{blog_identifier}/blocks/bulk",
            data={
                "blocked_tumblelogs": blocked_tumblelogs,
            },
        )

    def retrieve_published_post(self, url: str) -> Post:
        post = Post.from_url(url)

        response = self.get(
            f"{post.blog_name}/posts",
            params={
                "id": post.id,
                "npf": True,
            },
        )
        return ResponseModel[PostResponse].model_validate_json(response.text).response.posts[0]

    def get_notes(self, post: Post, before_timestamp: int | None, mode: NotesMode) -> NoteResponse:
        response = self.get(
            f"{post.blog_name}/notes",
            params={
                "id": post.id,
                "before_timestamp": before_timestamp,
                "mode": mode,
            },
        )
        return ResponseModel[NoteResponse].model_validate_json(response.text).response

    def get_all_notes(self, post: Post, mode: NotesMode) -> Generator[Note]:
        before_timestamp = None
        while before_timestamp != DEFAULT_INT:
            response = self.get_notes(post, before_timestamp, mode)
            before_timestamp = response.links.next.query_params.before_timestamp
            yield from response.notes
