# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.4] - 2026-05-06

### Changed

- Remove `ignore: brands` from HACS action to meet HACS default store submission requirements
- Update `info.md` with accurate platform descriptions and correct repository URLs
- Bump version across `manifest.json` and `const.py`

## [0.4.3] - 2026-05-06

### Improved

- 100% test coverage across all modules

## [0.4.2] - 2026-05-06

### Fixed

- Updated integration icon to match NexBlue branding

## [0.4.1] - 2026-05-06

### Fixed

- Renamed `brands/` to `brand/` so the integration icon displays correctly in HA 2026.3+ and HACS

## [0.4.0] - 2026-05-06

### Added

- **Last Session sensors (diagnostic):** Last Session Start/End timestamps, Last Session Energy (kWh), Last Session Stop Reason
- **Charger configuration sensors (diagnostic):** Access Level, Phase Mode, UK Regulation Mode, Protocol Version
- **Energy Today** sensor (kWh, daily total — compatible with HA Energy Dashboard)
- NexBlue-style integration icon
- Full README rewrite with complete entity list and HACS quick-add button

### Fixed

- Corrected API field names verified against live API: `cable_lock_mode`, `cable_current_limit`, `access_level`, `phase_charging`

## [0.3.3] - 2026-05-05

### Changed

- Replace `async_timeout` with built-in `asyncio.timeout` (Python 3.11+)
- Remove unused `Config` import and redundant `async_setup` no-op from `__init__.py`
- Remove `aiohttp` from `manifest.json` requirements (it is a HA core dependency)

## [0.3.2] - 2026-05-05

### Fixed

- Fix Hassfest CI failure caused by URL in `translations/en.json` description string
- Fix test runner crash (`AttributeError: module 'pycares'`) by bumping `pytest-homeassistant-custom-component` to 0.13.316
- Sync `VERSION` constant in `const.py` to match `manifest.json`

### Changed

- Dependency updates: `pytest-homeassistant-custom-component`, `pip`, `coverage`, `ruff`, and various GitHub Actions

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

## [0.1.0] - 2025-07-13

### Added

- Basic NexBlue EV Charger integration
- Binary sensor platform for charger states
- Sensor platform for charger metrics
- Switch platform for charging control
- Configuration flow with authentication
- Cloud polling integration with NexBlue API
