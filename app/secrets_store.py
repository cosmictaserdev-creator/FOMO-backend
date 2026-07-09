from __future__ import annotations

import secrets

from dotenv import dotenv_values, set_key

import backend_path  # noqa: F401 -- sets up sys.path before backend_dir() use below

ENV_FILE = backend_path.backend_dir() / ".env"

REQUIRED_KEYS = ["SUPABASE_URL", "SUPABASE_KEY", "GROQ_API_KEY"]
ALL_KEYS = [
    "SUPABASE_URL",
    "SUPABASE_KEY",
    "GROQ_API_KEY",
    "REDDIT_CLIENT_ID",
    "REDDIT_CLIENT_SECRET",
    "REDDIT_USERNAME",
    "YOUTUBE_API_KEY",
]


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    return {k: v for k, v in dotenv_values(ENV_FILE).items() if v is not None}


def save_env(values: dict[str, str]) -> list[str]:
    """Writes values into backend/.env using dotenv's quoting-safe writer.

    Returns a list of missing required keys (empty if all present).
    """
    missing = [k for k in REQUIRED_KEYS if not values.get(k, "").strip()]
    if missing:
        return missing

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE.exists():
        ENV_FILE.touch()

    for key in ALL_KEYS:
        if key in values:
            set_key(str(ENV_FILE), key, values[key], quote_mode="always")

    return []


def get_or_create_api_auth_token() -> str:
    existing = load_env().get("API_AUTH_TOKEN")
    if existing:
        return existing
    token = secrets.token_urlsafe(32)
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE.exists():
        ENV_FILE.touch()
    set_key(str(ENV_FILE), "API_AUTH_TOKEN", token, quote_mode="always")
    return token
