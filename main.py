import uvicorn
import logging
import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_app_config
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import v1_router
from app.api.root import root_router

# ------------------------------------------------------------------
# GLOBAL LOGGING CONFIG (MUST COME FIRST)
# ------------------------------------------------------------------

app_config = get_app_config()

LOG_LEVEL = logging.DEBUG if app_config.general_config.development_mode else logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# LIFESPAN
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Dunistech Academy API...")
    yield
    logger.info("Shutdown complete")


# ------------------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------------------

app = FastAPI(
    title=app_config.general_config.site_name,
    description=app_config.general_config.site_description,
    version=app_config.general_config.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# @app.on_event("startup")
# async def startup_event():
#     for route in app.routes:
#         print(f"{route.methods} {route.path}")

# ------------------------------------------------------------------ 
# OPENAPI CUSTOMIZATION
# ------------------------------------------------------------------
# from fastapi.openapi.models import APIKey, APIKeyIn, SecuritySchemeType
from fastapi.openapi.utils import get_openapi
# Add custom OpenAPI security scheme
app.openapi_schema = None
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add refresh token security definition
    openapi_schema["components"]["securitySchemes"]["RefreshToken"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-Refresh-Token",
        "description": "Paste your Refresh Token here for testing refresh flow."
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ------------------------------------------------------------------
# CUSTOM EXCEPTION HANDLING
# ------------------------------------------------------------------

setup_exception_handlers(app, app_config)

# ------------------------------------------------------------------
# MIDDLEWARE
# ------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] 
    if app_config.general_config.development_mode
    else [
        "https://studentscores.simplylovely.ng",
        "https://dunistech.ng",
        "https://www.dunistech.ng",
    ],
    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# ------------------------------------------------------------------
# ROUTERS
# ------------------------------------------------------------------

app.include_router(root_router)
app.include_router(v1_router)


# ------------------------------------------------------------------
# APP RUNNER
# ------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", app_config.hosting_config.port))
    host = os.getenv("HOST", "127.0.0.1")  # <-- use localhost
    uvicorn.run(
        'main:app',  # <-- pass the app object directly
        host=host,
        port=port,
        reload=app_config.general_config.development_mode,
        access_log=True,
        log_level="debug" if app_config.general_config.development_mode else "info",
        workers=1 if not app_config.general_config.development_mode else None,  # optional, remove for dev
    )
