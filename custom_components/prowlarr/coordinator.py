from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    ProwlarrApiClient,
    ProwlarrAuthenticationError,
    ProwlarrConnectionError,
)
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

LOGGER = logging.getLogger(__name__)


class ProwlarrDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to manage fetching data from Prowlarr."""

    def __init__(self, hass: HomeAssistant, api: ProwlarrApiClient) -> None:
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api = api

    async def _async_update_data(self) -> dict:
        try:
            return await self.api.async_fetch_all()
        except ProwlarrAuthenticationError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except ProwlarrConnectionError as err:
            raise UpdateFailed(f"Connection failed: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err