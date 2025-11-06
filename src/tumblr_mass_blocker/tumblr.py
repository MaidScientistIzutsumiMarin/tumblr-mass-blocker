from dataclasses import asdict

from authlib.integrations.httpx_client import AsyncOAuth1Client

from tumblr_mass_blocker.models import Post, ResponseModel, Tokens


class TumblrClient(AsyncOAuth1Client):
    def __init__(self, tokens: Tokens) -> None:
        super().__init__(
            **asdict(tokens),
            base_url="https://api.tumblr.com/v2/blog",
        )

    async def block_a_list_of_blogs(self, blog_identifier: object, blocked_tumblelogs: list[str]) -> ResponseModel:
        response = await self.post(
            f"{blog_identifier}/blocks/bulk",
            data={
                "blocked_tumblelogs": blocked_tumblelogs,
            },
        )
        response.raise_for_status()
        return ResponseModel.model_validate_json(response.text)

    async def retrieve_published_post(self, url: str) -> Post:
        post = Post.from_url(url)

        response = await self.get(
            f"{post.blog_name}/posts",
            params={
                "id": post.id,
                "notes_info": True,
            },
        )
        response.raise_for_status()
        return ResponseModel.model_validate_json(response.text).response.posts[0]
