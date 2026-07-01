import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings:
    app_name = "FINDY API"
    api_prefix = "/v1"
    database_url = os.getenv(
        "FINDY_DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'storage' / 'findy_server.db'}",
    )
    admin_api_key = os.getenv("FINDY_ADMIN_API_KEY", "dev-admin-key")
    cors_origins = [
        origin.strip()
        for origin in os.getenv("FINDY_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]


settings = Settings()

