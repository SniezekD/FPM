import pathlib

import pytest


@pytest.fixture
def valid_config() -> pathlib.Path:
    """A frozen, test-owned copy of a valid config"""
    return pathlib.Path(__file__).parent / "data" / "valid_config.toml"