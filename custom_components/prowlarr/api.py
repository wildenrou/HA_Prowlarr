from __future__ import annotations

from typing import Any

from aiohttp import ClientError, ClientSession


class ProwlarrApiError(Exception):
    """Base API exception."""


class ProwlarrAuthenticationError(ProwlarrApiError):
    """Raised when API authentication fails."""


class ProwlarrConnectionError(ProwlarrApiError):
    """Raised when Prowlarr cannot be reached."""


class ProwlarrApiClient:
    """Async client for the Prowlarr API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        api_key: str,
        use_ssl: bool,
    ) -> None:
        self._session = session
        self._host = host
        self._port = port
        self._api_key = api_key
        self._use_ssl = use_ssl

    @property
    def base_url(self) -> str:
        scheme = "https" if self._use_ssl else "http"
        return f"{scheme}://{self._host}:{self._port}/api/v1"

    async def _get(self, endpoint: str) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"X-Api-Key": self._api_key}

        try:
            async with self._session.get(url, headers=headers, timeout=20) as resp:
                if resp.status in (401, 403):
                    raise ProwlarrAuthenticationError("Invalid API key")
                if resp.status >= 400:
                    text = await resp.text()
                    raise ProwlarrConnectionError(
                        f"Unexpected status {resp.status} from {url}: {text}"
                    )
                return await resp.json()
        except ProwlarrApiError:
            raise
        except ClientError as err:
            raise ProwlarrConnectionError(f"Connection error to {url}") from err

    async def async_validate(self) -> dict[str, Any]:
        """Validate connectivity/auth."""
        return await self._get("system/status")

    async def async_fetch_all(self) -> dict[str, Any]:
        """Fetch all data needed by the integration."""
        system_status = await self._get("system/status")
        health = await self._get("health")
        indexers = await self._get("indexer")
        indexer_status = await self._get("indexerstatus")
        applications = await self._get("application")
        download_clients = await self._get("downloadclient")

        summary = self._build_summary(
            system_status=system_status,
            health=health,
            indexers=indexers,
            indexer_status=indexer_status,
            applications=applications,
            download_clients=download_clients,
        )

        return {
            "online": True,
            "system_status": system_status,
            "health": health,
            "indexers": indexers,
            "indexer_status": indexer_status,
            "applications": applications,
            "download_clients": download_clients,
            "summary": summary,
        }

    def _build_summary(
        self,
        *,
        system_status: dict[str, Any],
        health: list[dict[str, Any]],
        indexers: list[dict[str, Any]],
        indexer_status: list[dict[str, Any]],
        applications: list[dict[str, Any]],
        download_clients: list[dict[str, Any]],
    ) -> dict[str, Any]:
        enabled_indexers = [i for i in indexers if i.get("enable", False)]

        torrent_indexers = [
            i for i in indexers if str(i.get("protocol", "")).lower() == "torrent"
        ]
        usenet_indexers = [
            i for i in indexers if str(i.get("protocol", "")).lower() == "usenet"
        ]

        unhealthy_ids: set[int] = set()
        unhealthy_names: list[str] = []

        for item in indexer_status:
            indexer_id = item.get("indexerId")
            has_issue = bool(item.get("warning")) or bool(item.get("error"))
            if has_issue and indexer_id is not None:
                unhealthy_ids.add(indexer_id)

        for indexer in enabled_indexers:
            if indexer.get("id") in unhealthy_ids:
                unhealthy_names.append(indexer.get("name", f"Indexer {indexer.get('id')}"))

        enabled_applications = [a for a in applications if a.get("enable", False)]
        enabled_download_clients = [d for d in download_clients if d.get("enable", False)]

        return {
            "indexers_total": len(indexers),
            "indexers_enabled": len(enabled_indexers),
            "indexers_healthy": len(enabled_indexers) - len(unhealthy_ids),
            "indexers_unhealthy": len(unhealthy_ids),
            "indexers_torrent": len(torrent_indexers),
            "indexers_usenet": len(usenet_indexers),
            "applications_total": len(applications),
            "applications_enabled": len(enabled_applications),
            "download_clients_total": len(download_clients),
            "download_clients_enabled": len(enabled_download_clients),
            "health_issues_total": len(health),
            "has_health_issues": len(health) > 0,
            "unhealthy_indexer_names": unhealthy_names,
            "version": system_status.get("version"),
            "instance_name": system_status.get("instanceName"),
            "app_name": system_status.get("appName"),
        }