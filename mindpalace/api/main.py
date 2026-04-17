import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from mindpalace.api.routes.auth import router as auth_router, verify_token
from mindpalace.api.routes.chat import router as chat_router
from mindpalace.api.routes.history import router as history_router
from mindpalace.api.routes.ingest import router as ingest_router
from mindpalace.api.ws import router as ws_router

# Paths that don't require user auth
_PUBLIC_PATHS = {"/api/auth/login", "/api/auth/register", "/api/auth/webauthn/login/begin", "/api/auth/webauthn/login/complete", "/api/health"}


def create_app() -> FastAPI:
    app = FastAPI(title="MindPalace", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        path = request.url.path

        # Skip auth for: public API paths, static assets, SPA files, OPTIONS preflight
        if (
            request.method == "OPTIONS"
            or path in _PUBLIC_PATHS
            or path.startswith("/assets/")
            or path.startswith("/api/ingest/")  # ingest uses its own X-Api-Key auth
            or not path.startswith("/api/")
        ):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or not verify_token(auth[7:]):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

        return await call_next(request)

    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(history_router)
    app.include_router(ingest_router)
    app.include_router(ws_router)

    @app.on_event("startup")
    def on_startup():
        from mindpalace.db import init_db
        init_db()

    # Serve frontend static files if they exist
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "web", "dist")
    static_dir = os.path.normpath(static_dir)
    if os.path.isdir(static_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="static-assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(static_dir, full_path)
            if full_path and os.path.isfile(file_path):
                return FileResponse(file_path)
            return FileResponse(os.path.join(static_dir, "index.html"))

    return app


app = create_app()
