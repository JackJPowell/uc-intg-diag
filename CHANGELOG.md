# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-11-08

### Added
- Initial release of diagnostic integration for Remote Two/3 devices
- Battery monitoring using psutil library
- Real-time battery percentage, charging status, and time remaining
- System diagnostics including CPU and memory usage
- Media player entity to display diagnostic information
  - Title field: Battery percentage, charging status, and time remaining
  - Artist field: CPU and memory usage statistics
- Automatic updates every 5 seconds
- Support for systems without batteries (graceful handling)
- Docker support for containerized deployment
