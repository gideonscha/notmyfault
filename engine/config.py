"""Load configuration from .env without echoing secrets.

No python-dotenv dependency; parses simple KEY=VALUE lines. Values are never
printed — repr of Config masks the token.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"
DATA_META = REPO_ROOT / "data" / "meta"


def _load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip("'\"")
    return values


@dataclass
class Config:
    access_token: str = field(repr=False)
    ad_account_id: str = ""
    api_version: str = "v23.0"

    def __repr__(self) -> str:  # never leak the token in logs/tracebacks
        return (
            f"Config(access_token=<{'set' if self.access_token else 'MISSING'}>, "
            f"ad_account_id={self.ad_account_id!r}, api_version={self.api_version!r})"
        )


def load_config() -> Config:
    env = _load_env_file(ENV_PATH)

    def get(key: str, default: str = "") -> str:
        return os.environ.get(key) or env.get(key) or default

    token = get("META_ACCESS_TOKEN")
    account = get("META_AD_ACCOUNT_ID")
    if account and not account.startswith("act_"):
        account = f"act_{account}"
    if not token:
        raise SystemExit(
            "META_ACCESS_TOKEN is not set. Copy .env.example to .env and fill it in "
            "(see brief §9 — lift from the magic-portraits-ads skill's fetch_ads.py). "
            "The token is read from .env or the environment; it is never stored in code."
        )
    if not account:
        raise SystemExit("META_AD_ACCOUNT_ID is not set in .env or the environment.")
    return Config(
        access_token=token,
        ad_account_id=account,
        api_version=get("META_API_VERSION", "v23.0"),
    )
