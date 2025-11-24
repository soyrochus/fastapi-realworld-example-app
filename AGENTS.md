You are an expert FastAPI and server-side rendered web UI developer.

CONTEXT
- There is already an existing FastAPI backend that exposes a Conduit-style API (RealWorld spec) mounted under the `/api` prefix.
- The API includes endpoints for:
  - Articles: listing, filtering, creating, reading, updating, deleting, favoriting/unfavoriting.
  - Comments: listing, creating, deleting for a given article.
  - Profiles: viewing a user profile, following/unfollowing.
  - Tags: listing tags.
  - Users: register, login, get/update current user (with token-based auth via `Authorization` header; API key security scheme is `APIKeyHeader`). :contentReference[oaicite:0]{index=0}
- The OpenAPI specification is already present in the project and the API implementation is assumed to be correct and complete. Do not change the API behavior (see api.json)

YOUR TASK
Implement a simple but attractive server-side rendered web UI inside the existing FastAPI application that consumes this API and provides a minimal blog-like front end.

GENERAL REQUIREMENTS
- Use FastAPI’s standard patterns:
  - Create a dedicated router for the web UI, e.g. `web_router`, mounted at the root path (`/`).
  - Use Jinja2 templates (or the existing templating setup, if any) for server-side rendering.
  - Organize templates in a `templates/` directory with sensible subfolders (e.g. `templates/layout.html`, `templates/articles/list.html`, etc.).
  - Use static files for CSS/JS under `static/` and mount them with FastAPI’s `StaticFiles`.
- The UI should be **server-side rendered first**, with minimal JavaScript, only where it clearly simplifies UX (e.g. form submit prevention is not mandatory; plain POST/redirect is fine).
- Styling:
  - Implement a simple, clean “Material-like” look using plain CSS (no heavy framework required).
  - Use a neutral color palette, cards, subtle elevation/shadows, rounded corners.
  - The result does not have to be pixel-perfect Material Design, but it should look modern and visually pleasant.

AUTHENTICATION & SESSION
- The backend’s auth API:
  - `POST /api/users` registers a new user.
  - `POST /api/users/login` logs in.
  - `GET /api/user` returns the current user (requires `Authorization` header).
  - `PUT /api/user` updates the current user. :contentReference[oaicite:1]{index=1}
- Implement a simple session handling mechanism for the web UI:
  - After successful login or registration, store the `token` from the API’s `UserResponse` in a secure HTTP cookie (e.g. `auth_token`) or in a server-side session structure.
  - For server-side calls from FastAPI to the API, always include `Authorization: Token <token>` where required by the OpenAPI spec.
  - Provide a “Log out” action that clears this session/cookie.
- If the user is not authenticated:
  - Pages requiring auth (create article, edit article, follow/unfollow, favorite/unfavorite, commenting) must redirect to the login page.

API USAGE (HIGH LEVEL)
- Use the existing API endpoints, **do not bypass them**:
  - Articles:
    - `GET /api/articles` (with optional query params `limit`, `offset`, `author`, `tag`, `favorited`) to list articles.
    - `GET /api/articles/feed` for the personalized feed (requires auth).
    - `GET /api/articles/{slug}` to view a single article.
    - `POST /api/articles` to create a new article.
    - `PUT /api/articles/{slug}` to update an existing article.
    - `DELETE /api/articles/{slug}` to delete an article.
    - `POST /api/articles/{slug}/favorite` and `DELETE /api/articles/{slug}/favorite` to favorite/unfavorite. :contentReference[oaicite:2]{index=2}
  - Comments:
    - `GET /api/articles/{slug}/comments` to list comments on an article.
    - `POST /api/articles/{slug}/comments` to create a new comment.
    - `DELETE /api/articles/{slug}/comments/{commentId}` to delete a comment. :contentReference[oaicite:3]{index=3}
  - Tags:
    - `GET /api/tags` to list tags.
  - Profiles:
    - `GET /api/profiles/{username}` to view a profile.
    - `POST /api/profiles/{username}/follow` / `DELETE /api/profiles/{username}/follow` to follow/unfollow.
- Use Python HTTP client (e.g. `httpx.AsyncClient` or `httpx.Client`) inside FastAPI routes to call the JSON API, then pass the parsed data to templates.

PAGES TO IMPLEMENT
Implement at least the following web pages and routes (all server-side rendered):

1. Home page (`GET /`)
   - Displays two tabs:
     - “Global Feed” → uses `GET /api/articles` with default parameters.
     - If user is logged in, “Your Feed” → uses `GET /api/articles/feed`.
   - Show a paginated list of articles:
     - Title, description, author username, created date, favorites count, and list of tags.
     - Each article title links to the article detail page (`/article/{slug}`).
   - On the right (sidebar or under list on small screens), show a tag list using `GET /api/tags`. Clicking a tag filters the article list using `GET /api/articles?tag=<tag>`.
   - Provide basic pagination using `limit` and `offset` query parameters.

2. Article detail page (`GET /article/{slug}`)
   - Uses `GET /api/articles/{slug}` and `GET /api/articles/{slug}/comments`.
   - Show article:
     - Title, body, tag list, author username and avatar (if image is provided), created/updated dates, favorite count, favorited status.
   - Actions:
     - If user is authenticated:
       - Button to favorite/unfavorite this article (uses `POST`/`DELETE` favorite endpoints).
       - If the current user is the article author:
         - “Edit” → navigate to article edit page.
         - “Delete” → confirm and delete article, then redirect to home page.
   - Comments section:
     - If authenticated: show a textarea form for adding a new comment via `POST /api/articles/{slug}/comments`.
     - List existing comments (body, author, created date).
     - If the current user is the comment author: show a “Delete” action using `DELETE /api/articles/{slug}/comments/{commentId}`.

3. New article page (`GET /article/new`, `POST /article/new`)
   - Requires authentication.
   - Show a form for:
     - Title (string, required).
     - Description (string, required).
     - Body (multiline text, required).
     - Tag list (e.g. comma-separated, then split into list).
   - On submit:
     - Call `POST /api/articles` with payload matching `NewArticleRequest` defined in the OpenAPI spec.
     - On success, redirect to the new article’s detail page.
   - Provide server-side validation and show error messages if the API returns validation errors.

4. Edit article page (`GET /article/{slug}/edit`, `POST /article/{slug}/edit`)
   - Requires authentication, and user must be the article’s author.
   - Pre-load existing article data via `GET /api/articles/{slug}`.
   - Use the same form layout as “New article”.
   - On submit, call `PUT /api/articles/{slug}` with `UpdateArticleRequest` payload and redirect back to the article detail page on success.

5. Authentication pages
   - Register (`GET /register`, `POST /register`):
     - Form fields: username, email, password.
     - Call `POST /api/users` with `NewUserRequest`.
     - On success: store token, redirect to home page.
   - Login (`GET /login`, `POST /login`):
     - Form fields: email, password.
     - Call `POST /api/users/login` with `LoginUserRequest`.
     - On success: store token, redirect to home page.
   - Logout (`POST /logout` or `GET /logout` that internally uses POST semantics):
     - Clear auth session/cookie and redirect to home page.

6. Profile page (`GET /profile/{username}`)
   - Uses `GET /api/profiles/{username}`.
   - Show profile info:
     - Username, bio, image (if available).
     - Follow/unfollow button:
       - If authenticated and viewing someone else’s profile:
         - Use `POST /api/profiles/{username}/follow` and `DELETE /api/profiles/{username}/follow`.
   - Optionally, below profile info:
     - Show tabs for “Authored articles” and “Favorited articles”:
       - Use `GET /api/articles?author={username}` and `GET /api/articles?favorited={username}`.

7. Settings page (`GET /settings`, `POST /settings`)
   - Requires authentication.
   - Uses `GET /api/user` to pre-fill the form with current user data.
   - Fields for username, email, bio, image (URL).
   - On submit, call `PUT /api/user` with `UpdateUserRequest`, update stored token if necessary, and redirect back to settings or profile.

TEMPLATES & LAYOUT
- Create a base layout template `layout.html`:
  - Contains `<head>` with CSS includes and a `<body>` with:
    - Top navigation bar with:
      - App name/logo (click → home).
      - Links: Home, New Article, Settings, Login/Register or current username.
    - A main content block (`{% block content %}`) for page-specific content.
  - Include flash message area to show error/success messages passed from routes.
- Each page template should extend `layout.html` and fill the `content` block.

UX & STYLING DETAILS
- Use a responsive layout that works on desktop and mobile:
  - For example, a centered main column with max width and responsive padding.
- Article list entries:
  - Render each article in a “card” with title, metadata, short description, tags, and favorites count.
- Buttons:
  - Use consistent styling (rounded, subtle shadows, clear hover states).
- Forms:
  - Label all inputs clearly.
  - Show validation errors and API error messages near the related field or at the top of the form.

ERROR HANDLING
- For API errors (non-2xx responses, validation errors from `HTTPValidationError`):
  - Parse the error payload and show a user-friendly message in the UI.
  - Do not crash the server route; instead, re-render the template with error messages and previously entered data.
- For unauthenticated access to protected pages:
  - Redirect to `/login` and optionally show a flash message like “Please log in to continue.”

ARCHITECTURE & CODE ORGANIZATION
- Keep web UI specific code separate from the pure API code:
  - Create a new module/package, e.g. `web/` or `ui/`, with:
    - `routes.py` for FastAPI routes related to SSR pages.
    - `dependencies.py` for helpers like “get current user from session”.
    - `services.py` for small wrappers around API calls (e.g. `get_articles`, `get_article`, `create_article`, etc.).
  - Keep templates in `templates/` and static assets in `static/`.
- Ensure that the main FastAPI app includes:
  - StaticFiles mount for `/static`.
  - Template engine configuration.
  - Inclusion of the web router.

TESTING & ACCEPTANCE
- Add at least basic tests for:
  - Rendering the home page.
  - Authenticated vs unauthenticated behavior for protected routes.
- The implementation is “done” when:
  - A user can:
    - Register, login, logout.
    - See global feed and tags.
    - Create, edit, delete their own articles.
    - Favorite/unfavorite articles.
    - Add and delete their own comments.
    - View profiles and follow/unfollow other users.
    - Update their own settings.
  - All of this happens through server-side rendered views powered by the existing FastAPI app and the `/api` endpoints.

IMPORTANT
- Do NOT modify the semantics of the existing API endpoints.
- Focus on implementing the web UI as described above, integrated into the existing FastAPI project structure.
- Prefer clarity and maintainability over cleverness.
