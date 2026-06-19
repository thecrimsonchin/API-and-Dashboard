"""Configuration loaded from environment variables (.env in development)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. "
            "Copy .env.example to .env and fill it in."
        )
    return value


@dataclass(frozen=True)
class Settings:
    base_url: str
    endpoint_version: str
    username: str
    password: str
    tenant: str
    branch: str
    inventory_history_gi: str
    host: str
    port: int

    @property
    def entity_url(self) -> str:
        """Base URL for the contract-based REST endpoint (Default endpoint)."""
        return f"{self.base_url}/entity/Default/{self.endpoint_version}"

    @property
    def auth_url(self) -> str:
        """Base URL for the auth (login/logout) endpoints."""
        return f"{self.base_url}/entity/auth"

    @property
    def odata_url(self) -> str:
        """Base URL for OData (used for Generic Inquiry reads)."""
        # Acumatica OData v4 lives under /t/<tenant>/api/odata or /odata depending
        # on the build. For 2024 R1 the tenant-scoped path is the documented one.
        return f"{self.base_url}/t/{self.tenant}/api/odata"


def get_settings() -> Settings:
    return Settings(
        base_url=_require("ACUMATICA_BASE_URL").rstrip("/"),
        endpoint_version=os.getenv("ACUMATICA_ENDPOINT_VERSION", "24.200.001").strip(),
        username=_require("ACUMATICA_USERNAME"),
        password=_require("ACUMATICA_PASSWORD"),
        tenant=_require("ACUMATICA_TENANT"),
        branch=os.getenv("ACUMATICA_BRANCH", "").strip(),
        inventory_history_gi=os.getenv(
            "ACUMATICA_INVENTORY_HISTORY_GI", "Inventory-Transaction-History"
        ).strip(),
        host=os.getenv("APP_HOST", "127.0.0.1").strip(),
        port=int(os.getenv("APP_PORT", "8000")),
    )
