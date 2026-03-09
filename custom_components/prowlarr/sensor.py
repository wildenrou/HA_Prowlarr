from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NAME
from .coordinator import ProwlarrDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ProwlarrSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[ProwlarrSensorDescription, ...] = (
    ProwlarrSensorDescription(
        key="indexers_total",
        name="Indexers",
        value_fn=lambda data: data["summary"]["indexers_total"],
    ),
    ProwlarrSensorDescription(
        key="indexers_enabled",
        name="Enabled Indexers",
        value_fn=lambda data: data["summary"]["indexers_enabled"],
    ),
    ProwlarrSensorDescription(
        key="indexers_healthy",
        name="Healthy Indexers",
        value_fn=lambda data: data["summary"]["indexers_healthy"],
    ),
    ProwlarrSensorDescription(
        key="indexers_unhealthy",
        name="Unhealthy Indexers",
        value_fn=lambda data: data["summary"]["indexers_unhealthy"],
    ),
    ProwlarrSensorDescription(
        key="indexers_torrent",
        name="Torrent Indexers",
        value_fn=lambda data: data["summary"]["indexers_torrent"],
    ),
    ProwlarrSensorDescription(
        key="indexers_usenet",
        name="Usenet Indexers",
        value_fn=lambda data: data["summary"]["indexers_usenet"],
    ),
    ProwlarrSensorDescription(
        key="applications_total",
        name="Applications",
        value_fn=lambda data: data["summary"]["applications_total"],
    ),
    ProwlarrSensorDescription(
        key="download_clients_total",
        name="Download Clients",
        value_fn=lambda data: data["summary"]["download_clients_total"],
    ),
    ProwlarrSensorDescription(
        key="health_issues_total",
        name="Health Issues",
        value_fn=lambda data: data["summary"]["health_issues_total"],
    ),
    ProwlarrSensorDescription(
        key="version",
        name="Version",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["summary"]["version"],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: ProwlarrDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ProwlarrSensorEntity(coordinator, entry, description)
        for description in SENSORS
    )


class ProwlarrSensorEntity(
    CoordinatorEntity[ProwlarrDataUpdateCoordinator], SensorEntity
):
    entity_description: ProwlarrSensorDescription

    def __init__(
        self,
        coordinator: ProwlarrDataUpdateCoordinator,
        entry: ConfigEntry,
        description: ProwlarrSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_has_entity_name = True
        self._attr_name = description.name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            name=NAME,
            model="Prowlarr",
            sw_version=coordinator.data["summary"].get("version"),
        )

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "health_issues_total":
            return {
                "health_messages": [
                    item.get("message")
                    for item in self.coordinator.data.get("health", [])
                    if item.get("message")
                ]
            }
        if self.entity_description.key == "indexers_unhealthy":
            return {
                "unhealthy_indexer_names": self.coordinator.data["summary"].get(
                    "unhealthy_indexer_names", []
                )
            }
        return None