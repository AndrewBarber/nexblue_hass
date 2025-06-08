"""Setup for tests."""
from setuptools import setup

setup(
    name="nexblue_hass",
    packages=["custom_components.nexblue_hass"],
    version="0.1.0",
    description="NexBlue Home Assistant Integration",
    python_requires=">=3.9",
    install_requires=[
        "aiohttp>=3.8.0",
        "homeassistant>=2023.10.0",
    ],
    include_package_data=True,
)
