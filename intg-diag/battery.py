"""Battery monitoring module."""

import asyncio
import logging
from typing import Any
import psutil
from pyee import AsyncIOEventEmitter

from const import BatteryState

_LOG = logging.getLogger(__name__)


class Events:
    """Battery monitor events."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    UPDATE = "update"
    ERROR = "error"


EVENTS = Events()


class BatteryMonitor:
    """Battery monitoring class using psutil."""

    def __init__(self, device_id: str, device_name: str, loop: asyncio.AbstractEventLoop):
        """Initialize the battery monitor."""
        self.identifier = device_id
        self.name = device_name
        self._loop = loop
        self.events = AsyncIOEventEmitter()
        
        # Battery state
        self._percent: int | None = None
        self._power_plugged: bool | None = None
        self._time_left: int | None = None  # seconds
        self._state: BatteryState = BatteryState.UNKNOWN
        
        # System info
        self._cpu_percent: float | None = None
        self._memory_percent: float | None = None
        
        self._update_task: asyncio.Task | None = None
        self._connected = False

    @property
    def percent(self) -> int | None:
        """Get battery percentage."""
        return self._percent

    @property
    def power_plugged(self) -> bool | None:
        """Get power plugged status."""
        return self._power_plugged

    @property
    def time_left(self) -> int | None:
        """Get time left in seconds."""
        return self._time_left

    @property
    def state(self) -> BatteryState:
        """Get battery state."""
        return self._state

    @property
    def cpu_percent(self) -> float | None:
        """Get CPU usage percentage."""
        return self._cpu_percent

    @property
    def memory_percent(self) -> float | None:
        """Get memory usage percentage."""
        return self._memory_percent

    @property
    def connected(self) -> bool:
        """Get connection status."""
        return self._connected

    async def connect(self) -> None:
        """Start monitoring battery."""
        if self._connected:
            _LOG.debug("Battery monitor %s already connected", self.identifier)
            return

        _LOG.info("Starting battery monitor: %s", self.name)
        
        try:
            # Initial update
            await self._update_battery_info()
            
            self._connected = True
            self.events.emit(EVENTS.CONNECTED, self.identifier)
            
            # Start update task
            self._update_task = self._loop.create_task(self._update_loop())
            
        except Exception as ex:
            _LOG.error("Failed to connect battery monitor %s: %s", self.identifier, ex)
            self.events.emit(EVENTS.ERROR, self.identifier, f"Connection failed: {ex}")
            raise

    async def disconnect(self) -> None:
        """Stop monitoring battery."""
        if not self._connected:
            return

        _LOG.info("Stopping battery monitor: %s", self.name)
        
        # Cancel update task
        if self._update_task and not self._update_task.done():
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        self._connected = False
        self.events.emit(EVENTS.DISCONNECTED, self.identifier)

    async def _update_loop(self) -> None:
        """Periodically update battery information."""
        while self._connected:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                await self._update_battery_info()
            except asyncio.CancelledError:
                break
            except Exception as ex:
                _LOG.error("Error updating battery info: %s", ex)
                self.events.emit(EVENTS.ERROR, self.identifier, f"Update failed: {ex}")

    async def _update_battery_info(self) -> None:
        """Update battery information from psutil."""
        update_data: dict[str, Any] = {}
        
        try:
            # Get battery info
            battery = psutil.sensors_battery()
            
            if battery is not None:
                # Update battery percentage
                if battery.percent != self._percent:
                    self._percent = int(battery.percent)
                    update_data["percent"] = self._percent
                
                # Update power plugged status
                if battery.power_plugged != self._power_plugged:
                    self._power_plugged = battery.power_plugged
                    update_data["power_plugged"] = self._power_plugged
                
                # Update time left (convert to minutes for display)
                time_left = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                if time_left != self._time_left:
                    self._time_left = time_left
                    update_data["time_left"] = self._time_left
                
                # Determine state
                if battery.power_plugged:
                    if battery.percent >= 100:
                        new_state = BatteryState.FULL
                    else:
                        new_state = BatteryState.CHARGING
                else:
                    new_state = BatteryState.DISCHARGING
                
                if new_state != self._state:
                    self._state = new_state
                    update_data["state"] = self._state
            else:
                _LOG.warning("No battery found on this system")
                self._state = BatteryState.UNKNOWN
                update_data["state"] = self._state
            
            # Get CPU usage
            cpu = psutil.cpu_percent(interval=0.1)
            if cpu != self._cpu_percent:
                self._cpu_percent = cpu
                update_data["cpu_percent"] = self._cpu_percent
            
            # Get memory usage
            memory = psutil.virtual_memory().percent
            if memory != self._memory_percent:
                self._memory_percent = memory
                update_data["memory_percent"] = self._memory_percent
            
            # Emit update event if there are changes
            if update_data:
                self.events.emit(EVENTS.UPDATE, self.identifier, update_data)
                
        except Exception as ex:
            _LOG.error("Error reading battery info: %s", ex)
            raise

    def get_diagnostics(self) -> dict[str, Any]:
        """Get current diagnostic information."""
        return {
            "battery_percent": self._percent,
            "power_plugged": self._power_plugged,
            "time_left_seconds": self._time_left,
            "battery_state": self._state.value if self._state else "unknown",
            "cpu_percent": self._cpu_percent,
            "memory_percent": self._memory_percent,
        }
