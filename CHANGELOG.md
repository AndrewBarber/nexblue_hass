# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2025-12-06

### Fixed

- **Cable Lock Sensors Not Appearing** - Fixed API field names that prevented sensors from being discovered
- **Correct API Field Names** - Changed `cable_lock_mode` → `is_always_lock` (actual API field)
- **Sensor Implementation** - Updated all sensors to use proper API field references
- **Test Data** - Fixed test data to match actual NexBlue API specification
- **Binary Sensor Logic** - Updated cable locked binary sensor to use correct field

### Technical

- Verified against latest NexBlue API specification
- All cable lock sensors now read from actual API data fields
- Tests updated to reflect correct API field structure
- Pre-commit hooks and code quality checks pass

### Notes

- v0.3.0 cable lock sensors were non-functional due to incorrect API field names
- Users should upgrade to v0.3.1 for working cable lock monitoring
- No new features added - this is a bugfix release

## [0.3.0] - 2025-12-06

### Added

- **Cable Lock Sensors** - New sensors to monitor NexBlue charger cable lock status
- **Cable Lock Mode Sensor** - Shows current lock mode (0=lock_while_charging, 1=always_locked)
- **Cable Current Limit Sensor** - Displays cable current capacity (0-32A, 0 means not plugged)
- **Cable Locked Binary Sensor** - Quick binary indicator for cable lock status
- **Comprehensive Testing** - 8 new tests for cable lock functionality
- **Proper Error Handling** - Graceful handling of missing or invalid cable lock data

### Technical

- Enhanced sensor platform with cable lock monitoring capabilities
- Extended binary sensor platform with cable lock status entity
- Maintained 97.81% test coverage (144/144 tests passing)
- Read-only sensors based on available NexBlue API endpoints
- Updated version to 0.3.0 with comprehensive changelog

### Notes

- Cable lock control is not available via NexBlue API - sensors provide status monitoring only
- Users can now monitor cable lock status directly from Home Assistant
- All sensors include proper entity categorization and diagnostic icons

## [0.2.0] - 2025-12-06

### Added

- **Charging Current Limit Control** - New number platform to adjust charging current limit from Home Assistant
- Users can now set current limit from 6A to 32A in 1A increments
- Real-time feedback and updates after setting values
- Comprehensive error handling and API validation
- Full integration with existing NexBlue charger entities

### Technical

- Added `async_set_current_limit()` API method
- Created `NexBlueCurrentLimitNumber` entity in new number.py platform
- Added NUMBER platform to const.py PLATFORMS list
- Comprehensive test coverage (16 new tests + 6 new API tests)
- Overall test coverage: 97.81% (exceeds 90% requirement)

### Fixed

- Resolved GitHub Issue #21: "Charging current limit" feature request
- Users can now adjust charging current limit directly from Home Assistant UI

## [0.1.0] - Initial Release

### Added

- Basic NexBlue EV Charger integration
- Binary sensor platform for charger states
- Sensor platform for charger metrics
- Switch platform for charging control
- Configuration flow with authentication
- Cloud polling integration with NexBlue API
