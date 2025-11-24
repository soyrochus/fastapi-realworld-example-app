from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.web.services import fetch_current_user
from app.web.utils import AUTH_COOKIE, FLASH_COOKIE, format_date, get_flash

templates = Jinja2Templates(directory="templates")
templates.env.filters["date"] = format_date


def get_auth_token(request: Request) -> str | None:
    return request.cookies.get(AUTH_COOKIE)


async def get_current_user(request: Request) -> dict[str, Any] | None:
    if hasattr(request.state, "current_user"):
        return request.state.current_user
    token = get_auth_token(request)
    if not token:
        request.state.current_user = None
        return None
    user = await fetch_current_user(request, token)
    request.state.current_user = user
    return user


async def render(
    request: Request, template_name: str, context: dict[str, Any] | None = None, status_code: int = 200
):
    context = context or {}
    flash = get_flash(request)
    current_user = await get_current_user(request)
    merged_context = {"request": request, "current_user": current_user, "flash": flash} | context
    response = templates.TemplateResponse(template_name, merged_context, status_code=status_code)
    if flash:
        response.delete_cookie(FLASH_COOKIE)
    return response

