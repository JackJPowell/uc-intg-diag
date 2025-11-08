# uc-intg-diag
Diagnostic integration for Remote Two/3 devices

## Overview

This integration monitors battery health and provides diagnostic information to help identify battery life issues on your Remote Two/3 device. It uses the `psutil` Python library to gather system information and displays it through a media player entity.

## Features

- **Real-time Battery Monitoring**: Track battery percentage, charging status, and estimated time remaining
- **System Diagnostics**: Monitor CPU and memory usage to identify potential battery drains
- **Visual Display**: Information is displayed through the media player entity:
  - **Title**: Shows battery percentage, charging status, and time remaining
  - **Artist**: Displays CPU and memory usage statistics

## Installation

1. Add the integration to your Remote Two/3 device
2. The integration will automatically start monitoring your device's battery
3. View the diagnostic information on your media player entity

## Requirements

- Python 3.11+
- Remote Two/3 with Core API 0.20.0+

## Dependencies

- `ucapi==0.3.1` - Unfolded Circle API
- `psutil>=5.9.0` - System and process utilities (for battery monitoring)
- `aiohttp>=3.0.0,<4.0.0` - Async HTTP client
- `pyee~=12.0.0` - Event emitter
- `async-timeout>=5.0.1` - Async timeout utilities

## Usage

Once installed, the integration creates a media player entity called "Battery Monitor" that displays:

- **Battery Information** (Title field):
  - Current battery percentage
  - Charging status (⚡ Charging / ✓ Full)
  - Time remaining when discharging

- **System Information** (Artist field):
  - CPU usage percentage
  - Memory usage percentage

The information updates automatically every 5 seconds.

## Development

### Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export UC_CONFIG_HOME="./config"
export UC_LOG_LEVEL="DEBUG"

# Run the integration
python3 intg-diag/driver.py
```

### Docker

```bash
# Build the image
docker build -t uc-intg-diag .

# Run the container
docker run -v ./config:/config uc-intg-diag
```

## License

Mozilla Public License Version 2.0

## Author

Jack Powell - jackjpowell@gmail.com
