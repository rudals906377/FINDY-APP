from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db, seed_db
from .routers import admin, content, notices, points, reports, users


def create_app() -> FastAPI:
    init_db()
    seed_db()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="FINDY2 커뮤니티 운영 API",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(users.router, prefix=settings.api_prefix)
    app.include_router(notices.router, prefix=settings.api_prefix)
    app.include_router(content.router, prefix=settings.api_prefix)
    app.include_router(reports.router, prefix=settings.api_prefix)
    app.include_router(points.router, prefix=settings.api_prefix)
    app.include_router(admin.router, prefix=settings.api_prefix)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "findy_server"}

    return app


app = create_app()

