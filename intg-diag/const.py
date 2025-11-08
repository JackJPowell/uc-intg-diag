"""Constants for the diagnostic integration."""

from enum import Enum

# Battery states
class BatteryState(Enum):
    """Battery power states."""
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FULL = "full"
    UNKNOWN = "unknown"

# Update intervals
UPDATE_INTERVAL = 5  # seconds

# Entity types
DOMAIN = "diagnostic"
