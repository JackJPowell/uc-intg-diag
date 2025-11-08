# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Remote Two/3 Device                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Unfolded Circle Remote Interface            │    │
│  │                                                      │    │
│  │  Displays:                                          │    │
│  │  ┌──────────────────────────────────────────┐      │    │
│  │  │  Media Player Entity                     │      │    │
│  │  │  ┌────────────────────────────────────┐  │      │    │
│  │  │  │ Title:  Battery: 75% | ⚡ Charging │  │      │    │
│  │  │  │ Artist: CPU: 12.5% | Memory: 45.2% │  │      │    │
│  │  │  └────────────────────────────────────┘  │      │    │
│  │  └──────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│                          │ UC API                            │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Integration Driver (driver.py)              │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ Event Management                              │  │    │
│  │  │  • Connect/Disconnect                         │  │    │
│  │  │  • Standby/Wake                               │  │    │
│  │  │  • Entity Subscriptions                       │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ Entity Management                             │  │    │
│  │  │  • DiagnosticMediaPlayer                      │  │    │
│  │  │  • State Updates                              │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│                          │ Events                            │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │      Battery Monitor (battery.py)                   │    │
│  │  ┌──────────────────────────────────────────────┐  │    │
│  │  │ Monitoring Loop (5s interval)                 │  │    │
│  │  │  • Battery percentage                         │  │    │
│  │  │  • Charging status                            │  │    │
│  │  │  • Time remaining                             │  │    │
│  │  │  • CPU usage                                  │  │    │
│  │  │  • Memory usage                               │  │    │
│  │  └──────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↑                                   │
│                          │ psutil API                        │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │         System Resources (psutil)                   │    │
│  │  • sensors_battery()                                │    │
│  │  • cpu_percent()                                    │    │
│  │  • virtual_memory()                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Interaction Flow

### Initialization
1. `driver.py` initializes integration API
2. Loads device configuration from `config.py`
3. Creates `BatteryMonitor` instance for each device
4. Registers `DiagnosticMediaPlayer` entities
5. Connects event handlers

### Monitoring Loop
1. `BatteryMonitor` queries psutil every 5 seconds
2. Detects changes in battery/system metrics
3. Emits UPDATE events with changed data
4. `driver.py` receives events and updates entity attributes
5. `DiagnosticMediaPlayer` formats display data
6. Remote Two/3 UI shows updated information

### Event Handling
- **CONNECTED**: Battery monitor starts successfully
- **DISCONNECTED**: Battery monitor stops
- **UPDATE**: New battery/system data available
- **ERROR**: Monitoring error occurred

## Data Flow

```
System Metrics (psutil)
        ↓
  BatteryMonitor
        ↓
   UPDATE Event
        ↓
    driver.py
        ↓
Entity Attributes
        ↓
 UC API Protocol
        ↓
Remote Two/3 UI
```

## Module Responsibilities

### driver.py
- Integration lifecycle management
- Event routing and handling
- Entity state management
- UC API communication

### battery.py
- System resource monitoring via psutil
- Battery state tracking
- Event emission for updates
- Diagnostics data aggregation

### media_player.py
- Display formatting
- Command handling (ON/OFF)
- Attribute building
- User-friendly presentation

### config.py
- Device configuration storage
- JSON persistence
- Device lifecycle callbacks

### const.py
- Constants and enumerations
- Battery states
- Update intervals

### setup.py
- Integration setup flow
- Device initialization
- Configuration creation

## Dependencies

```
Integration
    ├── ucapi (0.3.1) - Unfolded Circle API
    │   ├── websockets
    │   └── zeroconf
    ├── psutil (5.9.0+) - System monitoring
    ├── aiohttp (3.x) - Async HTTP
    │   ├── yarl
    │   └── multidict
    └── pyee (12.0.0) - Event emitter
```

## Configuration Storage

```
UC_CONFIG_HOME/
    └── devices.json
        {
          "devices": [
            {
              "identifier": "battery_monitor",
              "name": "Battery Monitor",
              "enabled": true
            }
          ]
        }
```

## Update Frequency

- Battery monitoring: 5 seconds
- Display updates: On change
- Entity state sync: Real-time via events
