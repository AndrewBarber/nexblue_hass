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

## ✨ Features

**This integration sets up the following platforms:**

| Platform        | Description                                               |
| --------------- | --------------------------------------------------------- |
| `binary_sensor` | 🟢 Show charger connection status and charging state      |
| `sensor`        | 📊 Display charging data, energy usage, and other metrics |
| `switch`        | 🔌 Control charging (start/stop)                          |

![example][exampleimg]

## 📱 Screenshots

![example][exampleimg]

## 📦 Installation

### 🏆 HACS (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (menu) → Custom repositories
   - Enter `https://github.com/AndrewBarber/nexblue_hass` as the repository URL
   - Select `Integration` as the category
   - Click Add
3. Click on "+ Explore & Download Repositories" and search for "NexBlue"
4. Click "Download" on the NexBlue integration
5. Restart Home Assistant

### 🔧 Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`)
2. If you do not have a `custom_components` directory (folder) there, you need to create it
3. In the `custom_components` directory (folder) create a new folder called `nexblue_hass`
4. Download _all_ the files from the `custom_components/nexblue_hass/` directory (folder) in this repository
5. Place the files you downloaded in the new directory (folder) you created
6. Restart Home Assistant

## ⚙️ Setup

1. In the Home Assistant UI go to "Configuration" → "Integrations"
2. Click "+" and search for "NexBlue"
3. Enter your NexBlue account credentials (the same ones you use for the NexBlue app)

## 🔐 Authentication

This integration requires your NexBlue account credentials to authenticate with the NexBlue API. Your credentials are stored locally in Home Assistant and are only used to authenticate with the NexBlue API.

## 🚧 Work in Progress

This integration is still under development! Features are being added and bugs are being fixed. If you encounter any issues, please report them on the [GitHub issues page](https://github.com/AndrewBarber/nexblue_hass/issues).

## 🤝 Contributions are welcome!

If you want to contribute to this project, please read the [Contribution guidelines](CONTRIBUTING.md). Even if you're not a Python expert (like me!), your input is valuable!

## 💖 Support My Work

[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

If you find this integration useful, consider buying me a coffee! It helps me continue developing and maintaining this project.

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
