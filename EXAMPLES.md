# Usage Examples

This document shows examples of how the battery diagnostic integration displays information on your Remote Two/3 device.

## Display Format

The integration uses a media player entity to display information:
- **Title field**: Battery information (percentage, status, time remaining)
- **Artist field**: System diagnostics (CPU and memory usage)

## Example Displays

### Scenario 1: Charging Battery
```
Title:  Battery: 75% | ⚡ Charging
Artist: CPU: 12.5% | Memory: 45.2%
```

### Scenario 2: Discharging with Time Remaining
```
Title:  Battery: 45% | 3h 25m left
Artist: CPU: 8.3% | Memory: 52.1%
```

### Scenario 3: Fully Charged
```
Title:  Battery: 100% | ✓ Full
Artist: CPU: 5.1% | Memory: 38.7%
```

### Scenario 4: Low Battery Warning
```
Title:  Battery: 15% | 45m left
Artist: CPU: 25.8% | Memory: 67.3%
```

### Scenario 5: No Battery Detected
```
Title:  No Battery Detected
Artist: CPU: 0.0% | Memory: 9.0%
```

## Interpreting the Information

### Battery Information (Title)
- **Percentage**: Current battery level (0-100%)
- **⚡ Charging**: Device is plugged in and charging
- **✓ Full**: Battery is fully charged
- **Time left**: Estimated time remaining on battery (only shown when discharging)

### System Diagnostics (Artist)
- **CPU**: Current CPU usage percentage - high values may indicate excessive processing
- **Memory**: Current memory usage percentage - high values may indicate memory leaks

## Troubleshooting Battery Life

### High CPU Usage
If CPU usage is consistently high (>50%), it may indicate:
- Background processes consuming resources
- Apps not properly closing
- System updates running

### High Memory Usage
If memory usage is consistently high (>80%), it may indicate:
- Too many apps running simultaneously
- Memory leaks in applications
- Insufficient memory for current workload

### Rapid Battery Drain
Monitor the display over time. If battery percentage drops quickly while:
- CPU usage is high: Close unnecessary apps
- Memory usage is high: Restart device to clear memory
- Both are low: Battery may need replacement

## Update Frequency

The display updates every 5 seconds with fresh data, allowing you to monitor changes in real-time.
