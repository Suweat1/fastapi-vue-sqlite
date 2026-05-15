from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / "backend" / ".env"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(ENV_FILE)


def _resolve_upload_dir(raw_value: str | None) -> Path:
    if not raw_value:
        return BASE_DIR / "backend" / "uploads"
    path = Path(raw_value)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


@dataclass(slots=True)
class Settings:
    app_name: str = "Campus Second-hand Market"
    api_prefix: str = "/api"
    database_url: str = field(default_factory=lambda: os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(BASE_DIR / 'backend.db').as_posix()}",
    ))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret-change-me"))
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_EXPIRE_MINUTES", "10080")))
    upload_dir: Path = field(default_factory=lambda: _resolve_upload_dir(os.getenv("UPLOAD_DIR")))
    cors_origins: list[str] = field(default_factory=lambda: [
        origin.strip()
        for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ])


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
