import json
from datetime import datetime
from typing import Any

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

AUTH_COOKIE = "auth_token"
FLASH_COOKIE = "flash_message"


def format_date(value: str | datetime | None) -> str:
    """Format an ISO date string or datetime for display."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value.strftime("%b %d, %Y")


def set_flash(response: Response, message: str, category: str = "info") -> None:
    payload = json.dumps({"message": message, "category": category})
    response.set_cookie(
        FLASH_COOKIE,
        payload,
        max_age=300,
        httponly=False,
        samesite="lax",
    )


def get_flash(request: Request) -> dict[str, Any] | None:
    raw = request.cookies.get(FLASH_COOKIE)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def redirect_with_message(
    url: str, message: str | None = None, status_code: int = 303, category: str = "info"
) -> RedirectResponse:
    response = RedirectResponse(url=url, status_code=status_code)
    if message:
        set_flash(response, message, category=category)
    return response

