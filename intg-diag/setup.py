"""Setup flow for diagnostic integration."""

import logging
from typing import Any

import config
import ucapi

_LOG = logging.getLogger(__name__)


async def driver_setup_handler(msg: ucapi.SetupDriver) -> ucapi.SetupAction:
    """
    Handle driver setup requests.

    :param msg: driver setup request
    :return: setup action
    """
    _LOG.debug("Setup handler called with msg: %s", msg)
    
    if msg.setup_data.get("action") == "setup":
        # Create default battery monitor device
        device = config.DiagnosticDevice(
            identifier="battery_monitor",
            name="Battery Monitor",
            enabled=True,
        )
        
        # Add device to configuration
        if config.devices:
            config.devices.add(device)
        
        return ucapi.SetupComplete()
    
    # Default: show setup page
    return ucapi.SetupComplete()
