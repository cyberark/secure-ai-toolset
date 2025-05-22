import pytest

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions


class DummyFileSecretsProvider:

    def __init__(self, namespace):
        self._file = namespace
        self._dict = {}

    def get_secret_dictionary(self):
        return self._dict

    def store_secret_dictionary(self, d):
        self._dict = dict(d)


@pytest.fixture
def temp_config(monkeypatch):
    # Patch FileSecretsProvider in ConfigManager to use DummyFileSecretsProvider
    from agent_guard_core import config
    monkeypatch.setattr(config.config_manager, "FileSecretsProvider",
                        DummyFileSecretsProvider)
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
    assert config["A"] == "1"


def test_overwrite_config_value(temp_config):
    manager = ConfigManager()
    manager.set_config_value("B", "first")
    manager.set_config_value("B", "second")
    assert manager.get_config_value("B") == "second"


def test_enum_keys():
    keys = ConfigurationOptions.__members__.keys()
    assert "SECRET_PROVIDER" in keys
    assert "CONJUR_AUTHN_LOGIN" in keys
