"""Runtime config: API key and base URL, never exposed via repr/str."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_BASE_URL = "https://api.typesafe.ai"


class MissingApiKeyError(RuntimeError):
    pass


@dataclass
class Config:
    api_key: str = field(repr=False)
    base_url: str = DEFAULT_BASE_URL

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or DEFAULT_BASE_URL).rstrip("/")

    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def __repr__(self) -> str:
        return f"Config(base_url={self.base_url!r})"

    __str__ = __repr__


def load_config() -> Config:
    key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise MissingApiKeyError("TYPESAFE_API_KEY is not set")
    return Config(api_key=key, base_url=os.environ.get("JEV_BASE_URL", DEFAULT_BASE_URL))
