from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import RedirectResponse, Response

from app.web.dependencies import get_auth_token, get_current_user, render
from app.web.services import (
    add_comment,
    create_article,
    delete_article,
    delete_comment,
    fetch_article,
    fetch_articles,
    fetch_comments,
    fetch_profile,
    fetch_tags,
    toggle_favorite,
    toggle_follow,
    update_article,
    update_user,
    login_user,
    register_user,
)
from app.web.utils import AUTH_COOKIE, redirect_with_message

router = APIRouter()


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        AUTH_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )


async def ensure_authenticated(request: Request) -> tuple[dict[str, Any], str] | RedirectResponse:
    user = await get_current_user(request)
    token = get_auth_token(request)
    if not user or not token:
        return redirect_with_message("/login", "Please log in to continue.")
    return user, token


@router.get("/", name="home")
async def home(
    request: Request,
    tab: str = "global",
    tag: Optional[str] = None,
    page: int = 1,
):
    current_user = await get_current_user(request)
    token = get_auth_token(request) if current_user else None
    limit = 10
    page = max(page, 1)
    offset = (page - 1) * limit
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if tag:
        params["tag"] = tag
    feed = tab == "feed" and token is not None
    articles_response, errors = await fetch_articles(request, params=params, token=token, feed=feed)
    tags = await fetch_tags(request)
    articles = (articles_response or {}).get("articles", [])
    articles_count = (articles_response or {}).get("articlesCount", 0)
    has_next = offset + limit < articles_count
    context = {
        "articles": articles,
        "articles_count": articles_count,
        "tags": tags,
        "active_tab": "feed" if feed else "global",
        "selected_tag": tag,
        "page": page,
        "has_next": has_next,
        "errors": errors,
    }
    return await render(request, "home.html", context)


@router.get("/article/new")
async def new_article_form(request: Request):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    return await render(request, "articles/form.html", {"form": {}, "errors": []})


@router.post("/article/new")
async def create_article_view(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    body: str = Form(...),
    tags: str = Form(""),
):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    _, token = auth
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    article_data = {
        "title": title,
        "description": description,
        "body": body,
        "tagList": tag_list,
    }
    article, errors = await create_article(request, token, article_data)
    if errors:
        return await render(
            request,
            "articles/form.html",
            {"form": article_data, "errors": errors},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = redirect_with_message(f"/article/{article['slug']}", "Article created!")
    return response


@router.get("/article/{slug}")
async def article_detail(request: Request, slug: str):
    token = get_auth_token(request)
    current_user = await get_current_user(request)
    article_payload, errors = await fetch_article(request, slug, token=token)
    if not article_payload:
        return await render(
            request,
            "article_detail.html",
            {"article": None, "errors": errors, "comments": []},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    article = article_payload.get("article")
    comments, comment_errors = await fetch_comments(request, slug, token=token)
    errors.extend(comment_errors)
    return await render(
        request,
        "article_detail.html",
        {"article": article, "comments": comments, "errors": errors, "current_user": current_user},
    )


@router.get("/article/{slug}/edit")
async def edit_article_form(request: Request, slug: str):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    user, token = auth
    article_payload, errors = await fetch_article(request, slug, token=token)
    if not article_payload:
        return await render(
            request,
            "articles/form.html",
            {"form": {}, "errors": errors},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    article = article_payload["article"]
    if article["author"]["username"] != user["username"]:
        return redirect_with_message(f"/article/{slug}", "You can only edit your own articles.", category="warning")
    form_data = {
        "title": article["title"],
        "description": article["description"],
        "body": article["body"],
        "tagList": article.get("tagList", []),
    }
    return await render(request, "articles/form.html", {"form": form_data, "errors": [], "slug": slug})


@router.post("/article/{slug}/edit")
async def edit_article_submit(
    request: Request,
    slug: str,
    title: str = Form(...),
    description: str = Form(...),
    body: str = Form(...),
    tags: str = Form(""),
):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    user, token = auth
    existing_payload, _ = await fetch_article(request, slug, token=token)
    if not existing_payload or existing_payload["article"]["author"]["username"] != user["username"]:
        return redirect_with_message(f"/article/{slug}", "You can only edit your own articles.", category="warning")
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    article_data = {
        "title": title,
        "description": description,
        "body": body,
        "tagList": tag_list,
    }
    updated_article, errors = await update_article(request, token, slug, article_data)
    if errors:
        return await render(
            request,
            "articles/form.html",
            {"form": article_data, "errors": errors, "slug": slug},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return redirect_with_message(f"/article/{updated_article['slug']}", "Article updated.")


@router.post("/article/{slug}/delete")
async def delete_article_view(request: Request, slug: str):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    user, token = auth
    article_payload, _ = await fetch_article(request, slug, token=token)
    if not article_payload or article_payload["article"]["author"]["username"] != user["username"]:
        return redirect_with_message(f"/article/{slug}", "You can only delete your own articles.", category="warning")
    errors = await delete_article(request, token, slug)
    if errors:
        return redirect_with_message(f"/article/{slug}", errors[0], category="error")
    return redirect_with_message("/", "Article deleted.")


@router.post("/article/{slug}/favorite")
async def favorite_article(request: Request, slug: str, action: str = Form("favorite")):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    _, token = auth
    favorite = action != "unfavorite"
    errors = await toggle_favorite(request, token, slug, favorite=favorite)
    if errors:
        return redirect_with_message(f"/article/{slug}", errors[0], category="error")
    return redirect_with_message(f"/article/{slug}", "Updated favorites.")


@router.post("/article/{slug}/comment")
async def add_comment_view(request: Request, slug: str, body: str = Form(...)):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    _, token = auth
    _, errors = await add_comment(request, token, slug, body)
    if errors:
        return redirect_with_message(f"/article/{slug}", errors[0], category="error")
    return redirect_with_message(f"/article/{slug}", "Comment added.")


@router.post("/article/{slug}/comment/{comment_id}/delete")
async def delete_comment_view(request: Request, slug: str, comment_id: int):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    _, token = auth
    errors = await delete_comment(request, token, slug, comment_id)
    if errors:
        return redirect_with_message(f"/article/{slug}", errors[0], category="error")
    return redirect_with_message(f"/article/{slug}", "Comment deleted.")


@router.get("/login")
async def login_form(request: Request):
    return await render(request, "auth/login.html", {"errors": [], "form": {}})


@router.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    user, errors = await login_user(request, email, password)
    if errors or not user:
        return await render(
            request,
            "auth/login.html",
            {"errors": errors or ["Login failed"], "form": {"email": email}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = redirect_with_message("/", "Welcome back!")
    set_auth_cookie(response, user["token"])
    return response


@router.get("/register")
async def register_form(request: Request):
    return await render(request, "auth/register.html", {"errors": [], "form": {}})


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
):
    user, errors = await register_user(request, username=username, email=email, password=password)
    if errors or not user:
        return await render(
            request,
            "auth/register.html",
            {"errors": errors or ["Registration failed"], "form": {"username": username, "email": email}},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = redirect_with_message("/", "Account created. Welcome!")
    set_auth_cookie(response, user["token"])
    return response


@router.post("/logout")
async def logout(request: Request):
    response = redirect_with_message("/", "Logged out.")
    response.delete_cookie(AUTH_COOKIE)
    return response


@router.get("/logout")
async def logout_get(request: Request):
    return await logout(request)


@router.get("/profile/{username}")
async def profile_view(
    request: Request,
    username: str,
    tab: str = "author",
    page: int = 1,
):
    current_user = await get_current_user(request)
    token = get_auth_token(request)
    profile, errors = await fetch_profile(request, username, token=token)
    if not profile:
        return await render(
            request,
            "profile.html",
            {"profile": None, "articles": [], "errors": errors},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    limit = 10
    page = max(page, 1)
    offset = (page - 1) * limit
    params: Dict[str, Any] = {"limit": limit, "offset": offset}
    if tab == "favorites":
        params["favorited"] = username
    else:
        params["author"] = username
    articles_payload, article_errors = await fetch_articles(request, params=params, token=token)
    errors.extend(article_errors)
    articles = (articles_payload or {}).get("articles", [])
    articles_count = (articles_payload or {}).get("articlesCount", 0)
    has_next = offset + limit < articles_count
    context = {
        "profile": profile,
        "articles": articles,
        "active_tab": tab,
        "page": page,
        "has_next": has_next,
        "errors": errors,
        "current_user": current_user,
    }
    return await render(request, "profile.html", context)


@router.post("/profile/{username}/follow")
async def follow_profile(request: Request, username: str, action: str = Form("follow")):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    user, token = auth
    if user["username"] == username:
        return redirect_with_message(f"/profile/{username}", "You cannot follow yourself.", category="warning")
    follow = action != "unfollow"
    errors = await toggle_follow(request, token, username, follow=follow)
    if errors:
        return redirect_with_message(f"/profile/{username}", errors[0], category="error")
    return redirect_with_message(f"/profile/{username}", "Profile updated.")


@router.get("/settings")
async def settings_form(request: Request):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    user, _ = auth
    form_data = {
        "username": user.get("username", ""),
        "email": user.get("email", ""),
        "bio": user.get("bio", ""),
        "image": user.get("image", ""),
    }
    return await render(request, "settings.html", {"form": form_data, "errors": []})


@router.post("/settings")
async def settings_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    bio: str = Form(""),
    image: str = Form(""),
    password: str = Form(""),
):
    auth = await ensure_authenticated(request)
    if isinstance(auth, RedirectResponse):
        return auth
    _, token = auth
    user_data: Dict[str, Any] = {"username": username, "email": email, "bio": bio or None, "image": image or None}
    if password:
        user_data["password"] = password
    user, errors = await update_user(request, token, user_data)
    if errors or not user:
        return await render(
            request,
            "settings.html",
            {"form": user_data, "errors": errors or ["Unable to update profile"]},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    response = redirect_with_message("/settings", "Settings updated.")
    set_auth_cookie(response, user["token"])
    return response
