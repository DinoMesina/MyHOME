"""Fixtures for MyHOME tests using pytest-homeassistant-custom-component."""
import pytest
from homeassistant.core import HomeAssistant

import platform
import asyncio
import warnings

try:
    from aiohttp.web_exceptions import NotAppKeyWarning
    warnings.filterwarnings("ignore", category=NotAppKeyWarning)
except ImportError:
    pass

# This fixture allows us to load custom components in tests
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    from pytest_socket import disable_socket
    # disable_socket()  # Temporarily disabled locally for Windows asyncio pipe creation issue
    yield

@pytest.fixture(autouse=True)
def ignore_third_party_warnings():
    """Ensure third-party aiohttp NotAppKeyWarning does not abort test runs under -W error."""
    import warnings
    try:
        from aiohttp.web_exceptions import NotAppKeyWarning
        warnings.filterwarnings("ignore", category=NotAppKeyWarning)
    except ImportError:
        pass
    yield

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    from pytest_socket import enable_socket
    enable_socket()
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

def pytest_configure(config):
    """Configure pytest to ignore third-party HA dependency warnings."""
    config.addinivalue_line(
        "filterwarnings",
        "ignore::aiohttp.web_exceptions.NotAppKeyWarning",
    )
    config.addinivalue_line(
        "filterwarnings",
        "ignore::DeprecationWarning:homeassistant.*",
    )

def pytest_sessionstart(session):
    """Set the event loop policy to Selector on Windows to avoid _ssock AttributeError."""
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Return snapshot assertion fixture with the Home Assistant extension."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)

