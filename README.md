# 🔌 NexBlue Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## 🌟 Welcome to the NexBlue Integration!

> 🚨 **Disclaimer:** I'm not a Python developer! This project is built with enthusiasm and a lot of trial and error. Expect some "vibe coding" along the way! 😅

This unofficial integration connects your [NexBlue](https://nexblue.com/) EV charging devices to Home Assistant, allowing you to monitor and control your chargers from your smart home dashboard.

![example][exampleimg]

## ✨ Features

**This integration sets up the following platforms:**

| Platform        | Description                                                                                  |
| --------------- | -------------------------------------------------------------------------------------------- |
| `binary_sensor` | 🟢 Charger connection, vehicle connection, charging state, and error status                  |
| `sensor`        | 📊 Power, energy, current, voltage, last session data, and charger configuration diagnostics |
| `number`        | 🔢 Adjust the charger current limit                                                          |
| `switch`        | 🔌 Start and stop charging                                                                   |

### Detailed Entity Information

#### Binary Sensors

| Entity                | Description                                           |
| --------------------- | ----------------------------------------------------- |
| **Connected**         | Whether the charger is connected to the NexBlue cloud |
| **Vehicle Connected** | Whether a vehicle is plugged in                       |
| **Charging**          | Whether the charger is actively charging              |
| **Error**             | Whether the charger is in an error state              |

#### Sensors

**Live data:**

| Entity                        | Unit | Description                                                       |
| ----------------------------- | ---- | ----------------------------------------------------------------- |
| **Charging State**            | —    | Human-readable charger state (e.g. Charging, Finished, Available) |
| **Power**                     | kW   | Current charging power                                            |
| **Energy (Session)**          | kWh  | Energy delivered in the current session                           |
| **Energy (Total / Lifetime)** | kWh  | Total energy delivered by the charger                             |
| **Energy Today**              | kWh  | Energy delivered today                                            |
| **Current Limit**             | A    | Active current limit                                              |
| **Network Status**            | —    | Connectivity type (WiFi, LTE, Ethernet)                           |
| **Voltage L1 / L2 / L3**      | V    | Per-phase voltage                                                 |
| **Current L1 / L2 / L3**      | A    | Per-phase current                                                 |
| **Circuit Fuse**              | A    | Installed circuit fuse rating                                     |
| **Cable Current Limit**       | A    | Maximum current supported by the connected cable                  |
| **Cable Lock Mode**           | —    | Cable locking behaviour (Lock While Charging / Always Locked)     |
| **LED Brightness**            | %    | Charger LED brightness level                                      |

**Last session (diagnostic):**

| Entity                       | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| **Last Session Start**       | Timestamp when the last session started                  |
| **Last Session End**         | Timestamp when the last session ended                    |
| **Last Session Energy**      | Energy delivered in the last session (kWh)               |
| **Last Session Stop Reason** | Why the last session ended (e.g. EVDisconnected, Remote) |

**Charger configuration (diagnostic):**

| Entity                 | Description                                             |
| ---------------------- | ------------------------------------------------------- |
| **Access Level**       | Whether charging is restricted to authorised users only |
| **Phase Mode**         | Single phase or three phase charging mode               |
| **UK Regulation Mode** | Whether UK smart charging regulation mode is enabled    |
| **Protocol Version**   | OCPP protocol version reported by the charger           |

#### Number

| Entity            | Range  | Description                      |
| ----------------- | ------ | -------------------------------- |
| **Current Limit** | 6–32 A | Set the maximum charging current |

#### Switch

| Entity       | Description                              |
| ------------ | ---------------------------------------- |
| **Charging** | Start or stop an active charging session |

## 📦 Installation

### 🏆 HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (menu) → Custom repositories
   - Enter `https://github.com/AndrewBarber/nexblue_hass` as the repository URL
   - Select `Integration` as the category
   - Click Add
3. Search for "NexBlue" and click Download
4. Restart Home Assistant

### 🔧 Manual Installation

1. Open the directory for your HA configuration (where `configuration.yaml` lives)
2. Create a `custom_components` directory if one doesn't exist
3. Inside `custom_components`, create a folder called `nexblue_hass`
4. Download all files from `custom_components/nexblue_hass/` in this repository into that folder
5. Restart Home Assistant

## ⚙️ Setup

1. In Home Assistant go to **Settings → Integrations**
2. Click **+ Add Integration** and search for "NexBlue"
3. Enter your NexBlue account credentials (the same ones used in the NexBlue app)

## 🔐 Authentication

Your credentials are stored locally in Home Assistant and are only used to authenticate with the NexBlue API.

The integration handles token refresh automatically:

- Access tokens expire after 1 day
- Refresh tokens expire after 30 days

## 🚧 Work in Progress

This integration is under active development. If you encounter any issues, please report them on the [GitHub issues page](https://github.com/AndrewBarber/nexblue_hass/issues).

## 🤝 Contributions Welcome

If you want to contribute, please read the [Contribution guidelines](CONTRIBUTING.md).

## 💖 Support My Work

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

If you find this integration useful, consider buying me a coffee!

## 🙏 Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

Code template was mainly taken from [@Ludeeus](https://github.com/ludeeus)'s [integration_blueprint][integration_blueprint] template.

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[buymecoffee]: https://www.buymeacoffee.com/andrewbarber
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[commits]: https://github.com/AndrewBarber/nexblue_hass/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40AndrewBarber-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/AndrewBarber/nexblue_hass.svg?style=for-the-badge
[releases]: https://github.com/AndrewBarber/nexblue_hass/releases
[user_profile]: https://github.com/AndrewBarber
