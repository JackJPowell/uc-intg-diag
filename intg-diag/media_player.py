"""Media-player entity for displaying battery diagnostics."""

import logging
from typing import Any
import asyncio

import ucapi
import ucapi.api as uc
from ucapi import MediaPlayer, media_player, EntityTypes

import battery
from config import DiagnosticDevice, create_entity_id
from const import BatteryState

_LOG = logging.getLogger(__name__)


class DiagnosticMediaPlayer(MediaPlayer):
    """Representation of a Diagnostic Media Player entity for displaying battery info."""

    def __init__(self, config_device: DiagnosticDevice, battery_monitor: battery.BatteryMonitor):
        """Initialize the diagnostic media player."""
        self._battery = battery_monitor
        self._config = config_device
        
        _LOG.debug("Diagnostic Media Player init for %s", config_device.name)
        
        entity_id = create_entity_id(config_device.identifier, EntityTypes.MEDIA_PLAYER)
        
        # Media player features - minimal set for display only
        features = [
            media_player.Features.ON_OFF,
        ]
        
        # Initial attributes
        attributes = self._build_attributes()
        
        super().__init__(
            entity_id,
            config_device.name,
            features,
            attributes=attributes,
            device_class=media_player.DeviceClasses.RECEIVER,
            cmd_handler=self.media_player_cmd_handler,
        )

    def _build_attributes(self) -> dict[str, Any]:
        """Build entity attributes from battery monitor data."""
        attributes = {}
        
        # Set state based on battery state
        if not self._battery.connected:
            attributes[media_player.Attributes.STATE] = media_player.States.UNAVAILABLE
        elif self._battery.state == BatteryState.CHARGING:
            attributes[media_player.Attributes.STATE] = media_player.States.PLAYING
        elif self._battery.state == BatteryState.DISCHARGING:
            attributes[media_player.Attributes.STATE] = media_player.States.PAUSED
        elif self._battery.state == BatteryState.FULL:
            attributes[media_player.Attributes.STATE] = media_player.States.ON
        else:
            attributes[media_player.Attributes.STATE] = media_player.States.UNKNOWN
        
        # Use title to show battery percentage and state
        title = self._format_title()
        attributes[media_player.Attributes.MEDIA_TITLE] = title
        
        # Use artist to show system diagnostics
        artist = self._format_artist()
        attributes[media_player.Attributes.MEDIA_ARTIST] = artist
        
        return attributes

    def _format_title(self) -> str:
        """Format the title field with battery information."""
        if self._battery.percent is None:
            return "No Battery Detected"
        
        percent = self._battery.percent
        state = self._battery.state.value if self._battery.state else "unknown"
        
        # Build title string
        title_parts = [f"Battery: {percent}%"]
        
        if self._battery.power_plugged:
            title_parts.append("⚡ Charging")
        elif state == "full":
            title_parts.append("✓ Full")
        else:
            # Show time remaining if available
            if self._battery.time_left and self._battery.time_left > 0:
                hours = self._battery.time_left // 3600
                minutes = (self._battery.time_left % 3600) // 60
                if hours > 0:
                    title_parts.append(f"{hours}h {minutes}m left")
                else:
                    title_parts.append(f"{minutes}m left")
        
        return " | ".join(title_parts)

    def _format_artist(self) -> str:
        """Format the artist field with system diagnostics."""
        artist_parts = []
        
        if self._battery.cpu_percent is not None:
            artist_parts.append(f"CPU: {self._battery.cpu_percent:.1f}%")
        
        if self._battery.memory_percent is not None:
            artist_parts.append(f"Memory: {self._battery.memory_percent:.1f}%")
        
        return " | ".join(artist_parts) if artist_parts else "System Info"

    async def media_player_cmd_handler(
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> ucapi.StatusCodes:
        """
        Handle media-player entity commands.

        :param entity: media-player entity
        :param cmd_id: command
        :param params: optional command parameters
        :return: status code
        """
        _LOG.info("Got %s command request: %s %s", entity.id, cmd_id, params if params else "")
        
        try:
            match cmd_id:
                case media_player.Commands.ON:
                    # Connect/start monitoring
                    if not self._battery.connected:
                        await self._battery.connect()
                    return ucapi.StatusCodes.OK
                    
                case media_player.Commands.OFF:
                    # Disconnect/stop monitoring
                    if self._battery.connected:
                        await self._battery.disconnect()
                    return ucapi.StatusCodes.OK
                    
                case _:
                    _LOG.warning("Unsupported command: %s", cmd_id)
                    return ucapi.StatusCodes.NOT_IMPLEMENTED
                    
        except Exception as ex:
            _LOG.error("Error executing command %s: %s", cmd_id, ex)
            return ucapi.StatusCodes.BAD_REQUEST
