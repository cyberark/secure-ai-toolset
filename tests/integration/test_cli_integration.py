import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_guard_core.cli import cli
from agent_guard_core.config.config_manager import ConfigurationOptions, SecretProviderOptions


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_config_home(monkeypatch):
    # Create a temporary directory and patch Path.home() to use it
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr("pathlib.Path.home", lambda: Path(temp_dir))
        yield Path(temp_dir)


def test_configure_set_and_get_secret_provider(runner, temp_config_home):
    # Iterate over all provider types and set/get each one
    for provider in SecretProviderOptions.get_keys():
        # Set a value using the CLI
        result = runner.invoke(
            cli,
            ['configure', 'set', '--provider', provider],
            input="\n"  # for any prompt
        )
        assert result.exit_code == 0

        # Get the value using the CLI
        result = runner.invoke(cli, [
            'configure', 'get', '--key',
            ConfigurationOptions.SECRET_PROVIDER.name
        ])
        assert result.exit_code == 0
        output = result.output.strip()
        key, value = output.split("=")
        assert key == ConfigurationOptions.SECRET_PROVIDER.name
        assert value == provider


def test_configure_set_and_get_conjur_provider(runner, temp_config_home):
    # Set values using the CLI
    result = runner.invoke(cli, [
        'configure', 'set', '--provider',
        SecretProviderOptions.CONJUR_SECRET_PROVIDER.name,
        '--conjur_authn_login', 'user1'
    ],
                           input="\n")
    assert result.exit_code == 0

    # Get provider value
    result = runner.invoke(cli, [
        'configure', 'get', '--key', ConfigurationOptions.SECRET_PROVIDER.name
    ])
    assert result.exit_code == 0
    output = result.output.strip()
    key, value = output.split("=")
    assert key == ConfigurationOptions.SECRET_PROVIDER.name
    assert value == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name

    # Get conjur_authn_login value
    result = runner.invoke(cli,
                           ['configure', 'get', '--key', 'CONJUR_AUTHN_LOGIN'])
    assert result.exit_code == 0
    output = result.output.strip()
    key, value = output.split("=")
    assert key == "CONJUR_AUTHN_LOGIN"
    assert value == "user1"


def test_configure_get_nonexistent_key(runner, temp_config_home):
    # Try to get a key that does not exist
    result = runner.invoke(cli,
                           ['configure', 'get', '--key', 'NON_EXISTENT_KEY'])
    assert result.exit_code == 2
    assert "'--key': 'NON_EXISTENT_KEY' is not one of" in result.output
