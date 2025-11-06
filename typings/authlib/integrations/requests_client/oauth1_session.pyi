from authlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_HEADER
from authlib.oauth1.client import OAuth1Client
from requests import Session

class OAuth1Session(OAuth1Client, Session):
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
    def fetch_request_token(
        self,
        url: str,
        **kwargs: object,
    ) -> dict[str, str]: ...
    def create_authorization_url(
        self,
        url: str,
        request_token: str | None = None,
        **kwargs: object,
    ) -> str: ...
    def parse_authorization_response(
        self,
        url: str,
    ) -> dict[str, str]: ...
    def fetch_access_token(
        self,
        url: str,
        verifier: str | None = None,
        **kwargs: object,
    ) -> dict[str, str]: ...
