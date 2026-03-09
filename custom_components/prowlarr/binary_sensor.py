from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, NAME
from .coordinator import ProwlarrDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class ProwlarrBinarySensorDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool]


BINARY_SENSORS: tuple[ProwlarrBinarySensorDescription, ...] = (
    ProwlarrBinarySensorDescription(
        key="online",
        name="Online",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["online"],
    ),
    ProwlarrBinarySensorDescription(
        key="has_health_issues",
        name="Health Issues Present",
        value_fn=lambda data: data["summary"]["has_health_issues"],
    ),
    ProwlarrBinarySensorDescription(
        key="has_unhealthy_indexers",
        name="Unhealthy Indexers Present",
        value_fn=lambda data: data["summary"]["indexers_unhealthy"] > 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: ProwlarrDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        ProwlarrBinarySensorEntity(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class ProwlarrBinarySensorEntity(
    CoordinatorEntity[ProwlarrDataUpdateCoordinator], BinarySensorEntity
):
    entity_description: ProwlarrBinarySensorDescription

    def __init__(
        self,
        coordinator: ProwlarrDataUpdateCoordinator,
        entry: ConfigEntry,
        description: ProwlarrBinarySensorDescription,
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
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.key == "has_health_issues":
            return {
                "health_messages": [
                    item.get("message")
                    for item in self.coordinator.data.get("health", [])
                    if item.get("message")
                ]
            }
        return None