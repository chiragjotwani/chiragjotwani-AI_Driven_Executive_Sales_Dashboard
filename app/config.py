from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency during bootstrap
    load_dotenv = None

try:
    import streamlit as st
except ImportError:  # pragma: no cover - streamlit may not be imported in tests
    st = None


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if load_dotenv and ENV_FILE.exists():
    load_dotenv(ENV_FILE)


def _get_secret(name: str, default: str = "") -> str:
    if st is not None:
        try:
            return str(st.secrets.get(name, os.getenv(name, default)))
        except Exception:  # pragma: no cover - streamlit runtime dependent
            pass
    return os.getenv(name, default)


@dataclass(frozen=True)
class AppConfig:
    data_path: Path = BASE_DIR / "data" / "raw" / "sales.csv"
    app_title: str = "AI-Powered Executive Sales Dashboard"
    openai_api_key: str = _get_secret("OPENAI_API_KEY", "")
    openai_model: str = _get_secret("OPENAI_MODEL", "gpt-4.1-mini")
    gemini_api_key: str = _get_secret("GEMINI_API_KEY", "")
    gemini_model: str = _get_secret("GEMINI_MODEL", "gemini-2.5-flash")
    powerbi_embed_url: str = _get_secret("POWERBI_EMBED_URL", "")
    powerbi_title: str = _get_secret("POWERBI_TITLE", "Power BI Executive Dashboard")
