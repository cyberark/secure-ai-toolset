import shutil
import tempfile
from pathlib import Path

import pytest

from agent_guard_core.config.config_manager import ConfigManager


@pytest.fixture
def temp_config_env(monkeypatch):
    # Create a temporary directory for config file
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "config.env"
    monkeypatch.setattr("agent_guard_core.config.config_manager.Path.home",
                        lambda: Path(temp_dir))
    yield config_path
    shutil.rmtree(temp_dir)


def test_config_manager_set_and_get(temp_config_env):
    manager = ConfigManager()
    manager.set_config_value("INTEGRATION_KEY", "integration_value")
    assert manager.get_config_value("INTEGRATION_KEY") == "integration_value"


def test_config_manager_persistence(temp_config_env):
    manager = ConfigManager()
    manager.set_config_value("PERSIST_KEY", "persist_value")
    # Create a new manager to simulate reload
    manager2 = ConfigManager()
    assert manager2.get_config_value("PERSIST_KEY") == "persist_value"


def test_config_manager_overwrite(temp_config_env):
    manager = ConfigManager()
    manager.set_config_value("OVERWRITE_KEY", "first")
    manager.set_config_value("OVERWRITE_KEY", "second")
    assert manager.get_config_value("OVERWRITE_KEY") == "second"
