#!/usr/bin/env python3
"""
Diagnostic integration driver for Remote Two/3 devices.

This integration monitors battery health and provides diagnostic information
to help identify battery life issues.

:copyright: (c) 2024 by Jack Powell
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
import sys
from typing import Any

import config
import setup
import ucapi
import ucapi.api as uc
from ucapi import media_player

import battery
from media_player import DiagnosticMediaPlayer
from config import DiagnosticDevice, device_from_entity_id

_LOG = logging.getLogger("driver")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)

# Global variables
api = uc.IntegrationAPI(_LOOP)
_configured_devices: dict[str, battery.BatteryMonitor] = {}


@api.listens_to(ucapi.Events.CONNECT)
async def on_r2_connect_cmd() -> None:
    """Connect all configured devices when Remote Two sends the connect command."""
    _LOG.debug("Client connect command: connecting device(s)")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    
    for device in _configured_devices.values():
        if not device.connected:
            await device.connect()


@api.listens_to(ucapi.Events.DISCONNECT)
async def on_r2_disconnect_cmd():
    """Disconnect all configured devices when Remote Two sends the disconnect command."""
    _LOG.debug("Client disconnect command: disconnecting device(s)")
    for device in _configured_devices.values():
        if device.connected:
            await device.disconnect()


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.

    Disconnect all battery monitor instances.
    """
    _LOG.debug("Enter standby event: disconnecting device(s)")
    for device in _configured_devices.values():
        if device.connected:
            await device.disconnect()


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all battery monitor instances.
    """
    _LOG.debug("Exit standby event: connecting device(s)")
    for device in _configured_devices.values():
        if not device.connected:
            await device.connect()


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    _LOG.debug("Subscribe entities event: %s", entity_ids)

    for entity_id in entity_ids:
        device_id = device_from_entity_id(entity_id)
        if device_id is None:
            continue
            
        if device_id in _configured_devices:
            device = _configured_devices[device_id]
            _LOG.info("Subscribing to device '%s'", device.name)
            
            # Update entity state
            if device.connected:
                state = media_player.States.ON
            else:
                state = media_player.States.UNAVAILABLE
            
            api.configured_entities.update_attributes(
                entity_id, {media_player.Attributes.STATE: state}
            )
            continue

        # Check if device exists in config
        device_config = config.devices.get(device_id) if config.devices else None
        if device_config:
            _add_configured_device(device_config)
        else:
            _LOG.error(
                "Failed to subscribe entity %s: no device configuration found", entity_id
            )


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """Handle entity unsubscription."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)
    for entity_id in entity_ids:
        device_id = device_from_entity_id(entity_id)
        if device_id is None:
            continue
        if device_id in _configured_devices:
            _configured_devices[device_id].events.remove_all_listeners()


async def on_device_connected(device_id: str):
    """Handle device connection."""
    _LOG.debug("Battery monitor connected: %s", device_id)
    
    if device_id not in _configured_devices:
        _LOG.warning("Battery monitor %s is not configured", device_id)
        return

    entity_id = f"media_player.{device_id}"
    configured_entity = api.configured_entities.get(entity_id)
    
    if configured_entity is None:
        _LOG.debug("Device connected: entity %s is not configured, ignoring", entity_id)
        return

    api.configured_entities.update_attributes(
        entity_id,
        {media_player.Attributes.STATE: media_player.States.ON},
    )
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)


async def on_device_disconnected(device_id: str):
    """Handle device disconnection."""
    _LOG.debug("Battery monitor disconnected: %s", device_id)

    entity_id = f"media_player.{device_id}"
    configured_entity = api.configured_entities.get(entity_id)
    
    if configured_entity is None:
        return

    api.configured_entities.update_attributes(
        entity_id,
        {media_player.Attributes.STATE: media_player.States.UNAVAILABLE},
    )


async def on_device_connection_error(device_id: str, message):
    """Handle device connection error."""
    _LOG.error("Battery monitor error for %s: %s", device_id, message)

    entity_id = f"media_player.{device_id}"
    configured_entity = api.configured_entities.get(entity_id)
    
    if configured_entity is None:
        return

    api.configured_entities.update_attributes(
        entity_id,
        {media_player.Attributes.STATE: media_player.States.UNAVAILABLE},
    )
    await api.set_device_state(ucapi.DeviceStates.ERROR)


async def on_device_update(device_id: str, update: dict[str, Any] | None) -> None:
    """
    Update attributes of configured media-player entity when battery info changes.

    :param device_id: Device identifier
    :param update: dictionary containing the updated properties
    """
    if update is None:
        return
        
    entity_id = f"media_player.{device_id}"
    
    configured_entity = api.available_entities.get(entity_id)
    if configured_entity is None:
        return

    if not isinstance(configured_entity, DiagnosticMediaPlayer):
        return

    attributes = {}
    
    # Rebuild display attributes with new data
    if "percent" in update or "state" in update or "power_plugged" in update or "time_left" in update:
        # Update title with battery info
        title = configured_entity._format_title()
        attributes[media_player.Attributes.MEDIA_TITLE] = title
        
        # Update state based on battery state
        monitor = _configured_devices.get(device_id)
        if monitor:
            if monitor.state == battery.BatteryState.CHARGING:
                attributes[media_player.Attributes.STATE] = media_player.States.PLAYING
            elif monitor.state == battery.BatteryState.DISCHARGING:
                attributes[media_player.Attributes.STATE] = media_player.States.PAUSED
            elif monitor.state == battery.BatteryState.FULL:
                attributes[media_player.Attributes.STATE] = media_player.States.ON
            else:
                attributes[media_player.Attributes.STATE] = media_player.States.UNKNOWN
    
    if "cpu_percent" in update or "memory_percent" in update:
        # Update artist with system diagnostics
        artist = configured_entity._format_artist()
        attributes[media_player.Attributes.MEDIA_ARTIST] = artist
    
    if attributes:
        if api.configured_entities.contains(entity_id):
            api.configured_entities.update_attributes(entity_id, attributes)
        else:
            api.available_entities.update_attributes(entity_id, attributes)


def _add_configured_device(device_config: DiagnosticDevice, connect: bool = False) -> None:
    """Add a configured device."""
    if device_config.identifier in _configured_devices:
        _LOG.debug("Device %s already configured", device_config.identifier)
        return

    _LOG.debug("Adding new device: %s (%s)", device_config.identifier, device_config.name)
    
    # Create battery monitor
    monitor = battery.BatteryMonitor(device_config.identifier, device_config.name, _LOOP)
    monitor.events.on(battery.EVENTS.CONNECTED, on_device_connected)
    monitor.events.on(battery.EVENTS.DISCONNECTED, on_device_disconnected)
    monitor.events.on(battery.EVENTS.ERROR, on_device_connection_error)
    monitor.events.on(battery.EVENTS.UPDATE, on_device_update)

    _configured_devices[device_config.identifier] = monitor

    async def start_connection():
        await monitor.connect()

    if connect:
        _LOOP.create_task(start_connection())

    _register_available_entities(device_config, monitor)


def _register_available_entities(
    device_config: DiagnosticDevice, monitor: battery.BatteryMonitor
) -> bool:
    """
    Register device entities as available.

    :param device_config: device configuration
    :param monitor: battery monitor instance
    :return: True if registered
    """
    _LOG.info("Registering available entities for %s", device_config.name)
    
    entity = DiagnosticMediaPlayer(device_config, monitor)
    
    if api.available_entities.contains(entity.id):
        api.available_entities.remove(entity.id)
    
    api.available_entities.add(entity)
    return True


def on_device_added(device: DiagnosticDevice) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New device added: %s", device)
    _add_configured_device(device, connect=False)


def on_device_removed(device: DiagnosticDevice | None) -> None:
    """Handle a removed device in the configuration."""
    if device is None:
        _LOG.debug("Configuration cleared, removing all configured devices")
        for device_monitor in _configured_devices.values():
            device_monitor.events.remove_all_listeners()
        _configured_devices.clear()
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        if device.identifier in _configured_devices:
            _LOG.debug("Removing device %s", device.identifier)
            device_monitor = _configured_devices.pop(device.identifier)
            device_monitor.events.remove_all_listeners()
            
            entity_id = f"media_player.{device.identifier}"
            api.configured_entities.remove(entity_id)
            api.available_entities.remove(entity_id)


async def main():
    """Start the integration driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("battery").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("config").setLevel(level)
    logging.getLogger("setup").setLevel(level)

    # Load device configuration
    config.devices = config.Devices(
        api.config_dir_path, on_device_added, on_device_removed
    )

    for device_config in config.devices.all():
        _add_configured_device(device_config)

    await api.init("driver.json", setup.driver_setup_handler)


if __name__ == "__main__":
    _LOOP.run_until_complete(main())
    _LOOP.run_forever()
