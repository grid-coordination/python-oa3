"""Authentication utilities for OpenADR 3 API."""

from __future__ import annotations

from typing import Generator

import httpx


class BearerAuth(httpx.Auth):
    """httpx Auth subclass that injects a Bearer token."""

    def __init__(self, token: str) -> None:
        self.token = token

    def auth_flow(
        self, request: httpx.Request
    ) -> Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


def fetch_token(
    base_url: str,
    client_id: str,
    client_secret: str,
    scopes: list[str] | None = None,
) -> str:
    """Fetch an OAuth2 access token using client credentials grant.

    Returns the access_token string.
    """
    token_url = f"{base_url.rstrip('/')}/auth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if scopes:
        data["scope"] = " ".join(scopes)

    with httpx.Client() as client:
        resp = client.post(token_url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]
