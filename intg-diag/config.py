"""Configuration management for the diagnostic integration."""

import json
import logging
import os
from dataclasses import dataclass
from typing import Callable

_LOG = logging.getLogger(__name__)


@dataclass
class DiagnosticDevice:
    """Diagnostic device configuration."""

    identifier: str
    name: str
    enabled: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "identifier": self.identifier,
            "name": self.name,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiagnosticDevice":
        """Create from dictionary."""
        return cls(
            identifier=data.get("identifier", "battery_monitor"),
            name=data.get("name", "Battery Monitor"),
            enabled=data.get("enabled", True),
        )


def create_entity_id(device_id: str, entity_type: str) -> str:
    """Create a unique entity identifier."""
    return f"{entity_type}.{device_id}"


def device_from_entity_id(entity_id: str) -> str | None:
    """Extract device id from entity id."""
    if "." in entity_id:
        return entity_id.split(".", 1)[1]
    return None


class Devices:
    """Manage configured devices."""

    def __init__(
        self,
        data_path: str,
        on_device_added: Callable[[DiagnosticDevice], None] | None = None,
        on_device_removed: Callable[[DiagnosticDevice | None], None] | None = None,
    ):
        """Initialize device storage."""
        self._data_path = data_path
        self._config_file = os.path.join(data_path, "devices.json")
        self._devices: dict[str, DiagnosticDevice] = {}
        self._on_device_added = on_device_added
        self._on_device_removed = on_device_removed
        self._load()

    def _load(self) -> None:
        """Load devices from storage."""
        if not os.path.exists(self._config_file):
            _LOG.info("No device configuration file found, creating default")
            # Create default device
            default_device = DiagnosticDevice(
                identifier="battery_monitor",
                name="Battery Monitor",
                enabled=True,
            )
            self._devices = {default_device.identifier: default_device}
            self._save()
            return

        try:
            with open(self._config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for device_data in data.get("devices", []):
                    device = DiagnosticDevice.from_dict(device_data)
                    self._devices[device.identifier] = device
            _LOG.info("Loaded %d device(s) from storage", len(self._devices))
        except Exception as ex:
            _LOG.error("Failed to load device configuration: %s", ex)
            # Create default device on error
            default_device = DiagnosticDevice(
                identifier="battery_monitor",
                name="Battery Monitor",
                enabled=True,
            )
            self._devices = {default_device.identifier: default_device}

    def _save(self) -> None:
        """Save devices to storage."""
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            data = {"devices": [device.to_dict() for device in self._devices.values()]}
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            _LOG.debug("Saved %d device(s) to storage", len(self._devices))
        except Exception as ex:
            _LOG.error("Failed to save device configuration: %s", ex)

    def all(self) -> list[DiagnosticDevice]:
        """Get all devices."""
        return list(self._devices.values())

    def get(self, device_id: str) -> DiagnosticDevice | None:
        """Get device by id."""
        return self._devices.get(device_id)

    def add(self, device: DiagnosticDevice) -> None:
        """Add or update device."""
        self._devices[device.identifier] = device
        self._save()
        if self._on_device_added:
            self._on_device_added(device)

    def remove(self, device_id: str) -> bool:
        """Remove device."""
        if device_id in self._devices:
            device = self._devices.pop(device_id)
            self._save()
            if self._on_device_removed:
                self._on_device_removed(device)
            return True
        return False

    def clear(self) -> None:
        """Remove all devices."""
        self._devices.clear()
        self._save()
        if self._on_device_removed:
            self._on_device_removed(None)


# Global device storage
devices: Devices | None = None
