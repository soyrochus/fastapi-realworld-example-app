from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from app.api.api import router
from app.core.config import settings
from app.web.routes import router as web_router

app = FastAPI(debug=settings.DEBUG, openapi_url="/api/docs.json", docs_url="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api",
)
app.include_router(web_router)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.openapi_schema = get_openapi(
    title="Conduit API",
    version="1.0.0",
    description="Conduit API",
    contact={"name": "RealWorld - Website", "url": "https://realworld.io/"},
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    routes=router.routes,
    servers=[{"url": "/api"}],
)
