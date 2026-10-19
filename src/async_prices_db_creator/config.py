"""Central configuration and project paths."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASE_URL = os.getenv("TECHNOLIFE_BASE_URL", "http://technolife.ir")
CATEGORY_LINK_TEXT = "قیمت گوشی"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))


def get_database_path(path: str | os.PathLike[str] | None = None) -> Path:
    """Return an absolute database path.

    Precedence: explicit argument, PHONE_PRICES_DB environment variable, then
    ``<project root>/data/Phone_prices.db``. Tilde and relative paths are
    expanded/resolved deliberately so the result does not depend on where the
    program was launched.
    """
    configured = path if path is not None else os.getenv("PHONE_PRICES_DB")
    if configured is None or str(configured).strip() == "":
        return PROJECT_ROOT / "data" / "Phone_prices.db"

    candidate = Path(configured).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate.resolve()


def request_headers() -> dict[str, str]:
    """Return an optional user-agent header supplied by the operator.

    If HTTP_USER_AGENT is unset, requests uses its normal default headers.
    """
    user_agent = os.getenv("HTTP_USER_AGENT", "").strip()
    return {"User-Agent": user_agent} if user_agent else {}
