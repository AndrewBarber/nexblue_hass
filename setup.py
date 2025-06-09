"""Setup for tests."""
from setuptools import setup

setup(
    name="nexblue_hass",
    packages=["custom_components.nexblue_hass"],
    version="0.1.0",
    description="NexBlue Home Assistant Integration",
    python_requires=">=3.13",
    install_requires=[
        "aiohttp>=3.8.0",
        "homeassistant>=2025.5.3",
    ],
    include_package_data=True,
)
