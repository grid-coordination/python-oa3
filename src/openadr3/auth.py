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
    token_url: str | None = None,
) -> str:
    """Fetch an OAuth2 access token using client credentials grant.

    Discovers the token endpoint via GET /auth/server unless token_url
    is provided explicitly. Returns the access_token string.
    """
    base = base_url.rstrip("/")

    with httpx.Client() as client:
        if not token_url:
            resp = client.get(f"{base}/auth/server")
            resp.raise_for_status()
            token_url = resp.json()["tokenURL"]

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if scopes:
            data["scope"] = " ".join(scopes)

        resp = client.post(token_url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]
