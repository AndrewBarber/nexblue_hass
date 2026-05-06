[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]][license]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

This unofficial integration connects your [NexBlue](https://nexblue.com/) EV charging devices to Home Assistant, allowing you to monitor and control your chargers from your smart home dashboard.

**This component will set up the following platforms.**

| Platform        | Description                                                                               |
| --------------- | ----------------------------------------------------------------------------------------- |
| `binary_sensor` | Charger connection, vehicle connection, charging state, and error status                  |
| `sensor`        | Power, energy, current, voltage, last session data, and charger configuration diagnostics |
| `number`        | Adjust the charger current limit                                                          |
| `switch`        | Start and stop charging                                                                   |

![example][exampleimg]

{% if not installed %}

## Installation

1. Click install.
1. Restart Home Assistant.
1. In the HA UI go to **Settings → Integrations**, click **+ Add Integration** and search for "NexBlue".
1. Enter your NexBlue account credentials (the same ones used in the NexBlue app).

{% endif %}

## Configuration is done in the UI

---

[buymecoffee]: https://www.buymeacoffee.com/andrewbarber
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[commits]: https://github.com/AndrewBarber/nexblue_hass/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[license]: https://github.com/AndrewBarber/nexblue_hass/blob/main/LICENSE
[license-shield]: https://img.shields.io/github/license/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40AndrewBarber-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[releases]: https://github.com/AndrewBarber/nexblue_hass/releases
[user_profile]: https://github.com/AndrewBarber
