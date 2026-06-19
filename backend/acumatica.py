"""Thin async client for the Acumatica contract-based REST API.

Targets Acumatica 2024 R1 (build 24.106.0018). Uses cookie/session auth:
POST /entity/auth/login establishes a session cookie that is reused for
subsequent reads; POST /entity/auth/logout releases the license seat.

The client lazily logs in on first use and transparently re-authenticates
once on a 401 (expired session). It is intended to be created once and shared
for the lifetime of the app.
"""
from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import Settings


class AcumaticaError(RuntimeError):
    """Raised when an Acumatica request fails after retrying auth."""


class AcumaticaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(timeout=30.0)
        self._logged_in = False
        self._lock = asyncio.Lock()

    async def _login(self) -> None:
        s = self._settings
        payload = {
            "name": s.username,
            "password": s.password,
            "tenant": s.tenant,
            "branch": s.branch,
            "locale": "",
        }
        resp = await self._client.post(f"{s.auth_url}/login", json=payload)
        if resp.status_code >= 400:
            raise AcumaticaError(
                f"Acumatica login failed ({resp.status_code}): {resp.text}"
            )
        self._logged_in = True

    async def _ensure_login(self) -> None:
        if not self._logged_in:
            async with self._lock:
                if not self._logged_in:
                    await self._login()

    async def logout(self) -> None:
        if self._logged_in:
            try:
                await self._client.post(f"{self._settings.auth_url}/logout")
            finally:
                self._logged_in = False
        await self._client.aclose()

    async def get_entity(
        self, entity: str, params: dict[str, Any] | None = None
    ) -> Any:
        """GET a contract-based REST entity from the Default endpoint.

        `params` accepts OData-style keys such as $filter, $select, $expand, $top.
        """
        url = f"{self._settings.entity_url}/{entity}"
        return await self._get_json(url, params)

    async def get_generic_inquiry(
        self, gi_name: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Read a Generic Inquiry exposed via OData.

        Inventory transaction history has no standard Default-endpoint entity,
        so it is read from a GI (see ACUMATICA_INVENTORY_HISTORY_GI).
        """
        url = f"{self._settings.odata_url}/{gi_name}"
        data = await self._get_json(url, params)
        # OData wraps rows in a "value" array.
        if isinstance(data, dict) and "value" in data:
            return data["value"]
        return data

    async def _get_json(self, url: str, params: dict[str, Any] | None) -> Any:
        await self._ensure_login()
        resp = await self._client.get(url, params=params)
        if resp.status_code == 401:
            # Session likely expired: re-login once and retry.
            self._logged_in = False
            await self._ensure_login()
            resp = await self._client.get(url, params=params)
        if resp.status_code >= 400:
            raise AcumaticaError(
                f"Acumatica GET {url} failed ({resp.status_code}): {resp.text}"
            )
        return resp.json()
