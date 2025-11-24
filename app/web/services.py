from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import Request


async def api_request(
    request: Request,
    method: str,
    path: str,
    token: str | None = None,
    **kwargs: Any,
) -> httpx.Response:
    headers = kwargs.pop("headers", {}) or {}
    if token:
        headers = {**headers, "Authorization": f"Token {token}"}
    transport = httpx.ASGITransport(app=request.app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url=str(request.base_url),
        timeout=10.0,
    ) as client:
        return await client.request(method, path, headers=headers, **kwargs)


def extract_errors(response: httpx.Response) -> List[str]:
    try:
        payload = response.json()
    except ValueError:
        return [response.text]
    errors: List[str] = []
    if isinstance(payload, dict) and "errors" in payload and isinstance(payload["errors"], dict):
        for field, messages in payload["errors"].items():
            if isinstance(messages, list):
                for msg in messages:
                    errors.append(f"{field}: {msg}")
            else:
                errors.append(f"{field}: {messages}")
    elif isinstance(payload, dict) and "message" in payload:
        errors.append(str(payload["message"]))
    elif isinstance(payload, dict):
        errors.append(str(payload))
    else:
        errors.append(str(payload))
    if not errors:
        errors.append("Unexpected error")
    return errors


async def fetch_current_user(request: Request, token: str) -> dict[str, Any] | None:
    response = await api_request(request, "GET", "/api/user", token=token)
    if response.status_code == 200:
        return response.json().get("user")
    return None


async def fetch_tags(request: Request) -> list[str]:
    response = await api_request(request, "GET", "/api/tags")
    if response.status_code == 200:
        return response.json().get("tags", [])
    return []


async def fetch_articles(
    request: Request,
    params: Dict[str, Any] | None = None,
    token: str | None = None,
    feed: bool = False,
) -> tuple[dict[str, Any] | None, List[str]]:
    path = "/api/articles/feed" if feed else "/api/articles"
    response = await api_request(request, "GET", path, params=params, token=token)
    if response.status_code == 200:
        return response.json(), []
    return None, extract_errors(response)


async def fetch_article(request: Request, slug: str, token: str | None = None) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(request, "GET", f"/api/articles/{slug}", token=token)
    if response.status_code == 200:
        return response.json(), []
    return None, extract_errors(response)


async def fetch_comments(request: Request, slug: str, token: str | None = None) -> tuple[list[dict[str, Any]], List[str]]:
    response = await api_request(request, "GET", f"/api/articles/{slug}/comments", token=token)
    if response.status_code == 200:
        return response.json().get("comments", []), []
    return [], extract_errors(response)


async def create_article(
    request: Request,
    token: str,
    article_data: Dict[str, Any],
) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "POST",
        "/api/articles",
        token=token,
        json={"article": article_data},
    )
    if response.status_code in (200, 201):
        return response.json().get("article"), []
    return None, extract_errors(response)


async def update_article(
    request: Request,
    token: str,
    slug: str,
    article_data: Dict[str, Any],
) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "PUT",
        f"/api/articles/{slug}",
        token=token,
        json={"article": article_data},
    )
    if response.status_code == 200:
        return response.json().get("article"), []
    return None, extract_errors(response)


async def delete_article(request: Request, token: str, slug: str) -> List[str]:
    response = await api_request(request, "DELETE", f"/api/articles/{slug}", token=token)
    if response.status_code in (200, 204):
        return []
    return extract_errors(response)


async def toggle_favorite(request: Request, token: str, slug: str, favorite: bool) -> List[str]:
    method = "POST" if favorite else "DELETE"
    response = await api_request(request, method, f"/api/articles/{slug}/favorite", token=token)
    if response.status_code in (200, 201):
        return []
    return extract_errors(response)


async def add_comment(request: Request, token: str, slug: str, body: str) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "POST",
        f"/api/articles/{slug}/comments",
        token=token,
        json={"comment": {"body": body}},
    )
    if response.status_code in (200, 201):
        return response.json().get("comment"), []
    return None, extract_errors(response)


async def delete_comment(request: Request, token: str, slug: str, comment_id: int) -> List[str]:
    response = await api_request(
        request,
        "DELETE",
        f"/api/articles/{slug}/comments/{comment_id}",
        token=token,
    )
    if response.status_code in (200, 204):
        return []
    return extract_errors(response)


async def login_user(request: Request, email: str, password: str) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "POST",
        "/api/users/login",
        json={"user": {"email": email, "password": password}},
    )
    if response.status_code == 200:
        return response.json().get("user"), []
    return None, extract_errors(response)


async def register_user(
    request: Request,
    username: str,
    email: str,
    password: str,
) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "POST",
        "/api/users",
        json={"user": {"username": username, "email": email, "password": password}},
    )
    if response.status_code in (200, 201):
        return response.json().get("user"), []
    return None, extract_errors(response)


async def fetch_profile(request: Request, username: str, token: str | None = None) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(request, "GET", f"/api/profiles/{username}", token=token)
    if response.status_code == 200:
        return response.json().get("profile"), []
    return None, extract_errors(response)


async def toggle_follow(request: Request, token: str, username: str, follow: bool) -> List[str]:
    method = "POST" if follow else "DELETE"
    response = await api_request(request, method, f"/api/profiles/{username}/follow", token=token)
    if response.status_code in (200, 201):
        return []
    return extract_errors(response)


async def update_user(
    request: Request,
    token: str,
    user_data: Dict[str, Any],
) -> tuple[dict[str, Any] | None, List[str]]:
    response = await api_request(
        request,
        "PUT",
        "/api/user",
        token=token,
        json={"user": user_data},
    )
    if response.status_code == 200:
        return response.json().get("user"), []
    return None, extract_errors(response)
