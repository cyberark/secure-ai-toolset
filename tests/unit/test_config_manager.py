import os
import pytest
from pathlib import Path
from typing import Dict, Optional

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions


class DummyFileSecretsProvider:
    """Mock implementation of FileSecretsProvider for testing."""
    
    # Class variable to persist data between instances
    _shared_storage = {}

    def __init__(self, namespace):
        # Ensure the file exists
        Path(namespace).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(namespace):
            with open(namespace, "w"):
                pass  # Create empty file
        
    def connect(self) -> bool:
        """Mock connect implementation."""
        return True

    def store(self, key: str, value: str) -> None:
        """Mock implementation of store method."""
        DummyFileSecretsProvider._shared_storage[key] = value

    def get(self, key: str) -> Optional[str]:
        """Mock implementation of get method."""
        value = DummyFileSecretsProvider._shared_storage.get(key)
        if value is None:
            raise SecretNotFoundException(key)
        return value

    def delete(self, key: str) -> None:
        """Mock implementation of delete method."""
        if key in DummyFileSecretsProvider._shared_storage:
            del DummyFileSecretsProvider._shared_storage[key]

    def _parse_collection(self) -> Dict[str, str]:
        """Mock implementation to return all stored values."""
        return dict(DummyFileSecretsProvider._shared_storage)


@pytest.fixture
def temp_config(monkeypatch):
    # Patch FileSecretsProvider in ConfigManager to use DummyFileSecretsProvider
    from agent_guard_core import config
    monkeypatch.setattr(config.config_manager, "FileSecretsProvider",
                        DummyFileSecretsProvider)
    
    # Make sure the config directory exists for testing
    config_dir = Path.joinpath(Path.home(), '.agent_guard')
    config_dir.mkdir(parents=True, exist_ok=True)
    
    yield


def test_set_and_get_config_value(temp_config):
    manager = ConfigManager()
    manager.set_config_value("TEST_KEY", "test_value")
    assert manager.get_config_value("TEST_KEY") == "test_value"


def test_get_config_returns_dict(temp_config):
    manager = ConfigManager()
    manager.set_config_value("A", "1")
    config = manager.get_config()
    assert isinstance(config, dict)
    assert config.get("A") == "1"


def test_overwrite_config_value(temp_config):
    manager = ConfigManager()
    manager.set_config_value("B", "first")
    manager.set_config_value("B", "second")
    assert manager.get_config_value("B") == "second"


def test_enum_keys():
    keys = ConfigurationOptions.__members__.keys()
    assert "SECRET_PROVIDER" in keys
    assert "CONJUR_AUTHN_LOGIN" in keys


def test_nonexistent_config_value(temp_config):
    manager = ConfigManager()
    assert manager.get_config_value("NONEXISTENT_KEY") is None


def test_config_persistence_between_instances(temp_config):
    # First instance sets a value
    manager1 = ConfigManager()
    manager1.set_config_value("PERSISTENCE_TEST", "persistent_value")
    
    # Second instance should see the same value
    manager2 = ConfigManager()
    assert manager2.get_config_value("PERSISTENCE_TEST") == "persistent_value"
