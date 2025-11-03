from authlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_HEADER
from authlib.oauth1.client import OAuth1Client
from httpx import AsyncClient

class AsyncOAuth1Client(OAuth1Client, AsyncClient):  # pyright: ignore[reportIncompatibleMethodOverride]
    def __init__(
        self,
        client_id: str,
        client_secret: str | None = None,
        token: str | None = None,
        token_secret: str | None = None,
        redirect_uri: str | None = None,
        rsa_key: str | None = None,
        verifier: str | None = None,
        signature_method: str = SIGNATURE_HMAC_SHA1,  # noqa: PYI011
        signature_type: str = SIGNATURE_TYPE_HEADER,  # noqa: PYI011
        force_include_body: bool = False,
        **kwargs: object,
    ) -> None: ...
