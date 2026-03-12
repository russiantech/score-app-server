# ============================================================
# PATCH — main.py
#
# 1. Add StaticFiles mount (serves ./uploads/... over HTTP)
# 2. No APP_API_URL needed anywhere — it's computed from APP_DOMAIN + APP_PORT + APP_SSL
# ============================================================

# --- ADD to imports ---
from fastapi.staticfiles import StaticFiles
import os

# --- ADD after `app = FastAPI(...)`, before middleware ---

# ------------------------------------------------------------------
# STATIC / MEDIA FILES
# Serves uploaded files at:  {api_url}/uploads/<subdir>/<filename>
# e.g. http://localhost:8001/uploads/avatars/foo.jpg
#
# The path is driven entirely by:
#   APP_FILESYSTEM_BASE_PATH  (default: "./uploads")
# ------------------------------------------------------------------
_uploads_dir = app_config.hosting_config.content_delivery.filesystem_base_path
os.makedirs(_uploads_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


# ============================================================
# .env — SINGLE SOURCE OF TRUTH for address/port/URL
#
# These three vars are all you need.  Everything else is derived.
#
#   APP_DOMAIN=localhost          → used in api_url, cookie domain
#   APP_PORT=8001                 → used in api_url, uvicorn bind port
#   APP_SSL=false                 → scheme (http vs https)
#
# api_url is COMPUTED:
#   http://localhost:8001         (ssl=false, non-standard port)
#   https://api.dunistech.ng      (ssl=true, port=443)
#
# DO NOT set APP_API_URL — it no longer exists in the config model.
# ============================================================

# Minimal .env example:
"""
APP_DOMAIN=localhost
APP_PORT=8001
APP_SSL=false
APP_FRONTEND_URL=http://localhost:5173
APP_FILESYSTEM_BASE_PATH=./uploads
APP_AUTH_JWT_SECRET_KEY=your-secret-here
"""

# Production .env example:
"""
APP_DOMAIN=api.dunistech.ng
APP_PORT=443
APP_SSL=true
APP_FRONTEND_URL=https://dunistech.ng
APP_FILESYSTEM_BASE_PATH=./uploads
APP_AUTH_JWT_SECRET_KEY=your-secret-here
"""