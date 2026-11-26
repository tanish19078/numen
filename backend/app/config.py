"""Environment and runtime configuration for Numen."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv_if_present() -> None:
    """Populate os.environ from root .env if not already set."""
    root_env = Path(__file__).resolve().parents[2] / ".env"
    if not root_env.exists():
        return
    for raw_line in root_env.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_flash_model: str
    gemini_pro_model: str
    db_path: str
    card_ttl_seconds: int
    drift_threshold: float
    hmac_secret: str


def get_settings() -> Settings:
    _load_dotenv_if_present()
    base_dir = Path(__file__).resolve().parents[1]
    raw_db = os.getenv("NUMEN_DB_PATH", str(base_dir / "numen.db"))
    db_path = str(Path(raw_db))
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_flash_model=os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash").strip(),
        gemini_pro_model=os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro").strip(),
        db_path=db_path,
        card_ttl_seconds=int(os.getenv("NUMEN_CARD_TTL_SECONDS", "60")),
        drift_threshold=float(os.getenv("NUMEN_ATTRIGUARD_DRIFT_THRESHOLD", "0.25")),
        hmac_secret=os.getenv("NUMEN_HMAC_SECRET", "numen-dev-sandbox-secret-change-in-prod"),
    )
