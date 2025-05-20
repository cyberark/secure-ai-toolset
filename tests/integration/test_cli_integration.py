import pytest
from click.testing import CliRunner

from agent_guard_core.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_configure_set_and_list(monkeypatch, tmp_path, runner):
    # Patch ConfigManager to use a dummy config dictionary in memory
    from agent_guard_core import cli as cli_module

    class DummyConfigManager:

        def __init__(self):
            self._config = {}

        def set_config_value(self, key, value):
            self._config[key] = value

        def get_config(self):
            return self._config

    monkeypatch.setattr(cli_module, "ConfigManager", DummyConfigManager)

    # Set a value
    result = runner.invoke(
        cli, ['configure', 'set', '--provider', 'FILE_SECRET_PROVIDER'])
    assert result.exit_code == 0

    # Set another value
    result = runner.invoke(cli, [
        'configure', 'set', '--provider', 'CONJUR_SECRET_PROVIDER',
        '--conjur_authn_login', 'user1'
    ])
    assert result.exit_code == 0

    # List values
    dummy_manager = DummyConfigManager()
    dummy_manager.set_config_value("SECRET_PROVIDER", "CONJUR_SECRET_PROVIDER")
    dummy_manager.set_config_value("CONJUR_AUTHN_LOGIN", "user1")
    monkeypatch.setattr(cli_module, "ConfigManager", lambda: dummy_manager)
    result = runner.invoke(cli, ['configure', 'list'])
    assert result.exit_code == 0
    assert "SECRET_PROVIDER=CONJUR_SECRET_PROVIDER" in result.output
    assert "CONJUR_AUTHN_LOGIN=user1" in result.output
