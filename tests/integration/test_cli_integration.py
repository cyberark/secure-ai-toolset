import os
import shutil
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from agent_guard_core.cli import cli
from agent_guard_core.config.config_manager import ConfigurationOptions
from agent_guard_core.credentials.enum import CredentialsProvider


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_config_home(monkeypatch):
    # Create a temporary directory and patch Path.home() to use it
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr("pathlib.Path.home", lambda: Path(temp_dir))
        yield Path(temp_dir)


@pytest.fixture
def temp_secrets_dir():
    """Create a temporary directory for storing test secrets"""
    # Create a temporary directory for secrets
    temp_dir = tempfile.mkdtemp()
    
    # Change to this directory so relative paths in tests use it
    original_dir = os.getcwd()
    os.chdir(temp_dir)
    
    yield temp_dir
    
    # Restore original directory and clean up
    os.chdir(original_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Clean environment variables that might interfere with CLI tests
    """
    env_vars_to_clear = [
        # AWS vars
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION',
        # GCP vars  
        'GCP_PROJECT_ID', 'GOOGLE_APPLICATION_CREDENTIALS',
        # Conjur vars
        'CONJUR_AUTHN_LOGIN', 'CONJUR_APPLIANCE_URL', 'CONJUR_AUTHENTICATOR_ID',
        'CONJUR_ACCOUNT', 'CONJUR_API_KEY'
    ]
    
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    
    yield


def test_configure_set_and_get_secret_provider(runner, temp_config_home):
    # Iterate over all provider types and set/get each one
    for provider in [provider.value for provider in CredentialsProvider]:
        # Set a value using the CLI
        result = runner.invoke(
            cli,
            ['config', 'set', '--provider', provider],
            input="\n"  # for any prompt
        )
        assert result.exit_code == 0

        # Get the value using the CLI
        result = runner.invoke(cli, [
            'config', 'get', '--key', ConfigurationOptions.SECRET_PROVIDER.name
        ])
        assert result.exit_code == 0
        output = result.output.strip()
        key, value = output.split("=")
        assert key == ConfigurationOptions.SECRET_PROVIDER.name
        assert value == provider


def test_configure_set_and_get_conjur_provider(runner, temp_config_home):
    # Set values using the CLI
    result = runner.invoke(cli, [
        'config', 'set', '--provider',
        CredentialsProvider.CONJUR.value,
        '--conjur-authn-login', 'user1'  # Changed from conjur_authn_login to conjur-authn-login
    ],
                           input="\n")
    assert result.exit_code == 0, f"Failed to set Conjur config: {result.output}"

    # Get provider value
    result = runner.invoke(
        cli,
        ['config', 'get', '--key', ConfigurationOptions.SECRET_PROVIDER.name])
    assert result.exit_code == 0
    output = result.output.strip()
    key, value = output.split("=")
    assert key == ConfigurationOptions.SECRET_PROVIDER.name
    assert value == CredentialsProvider.CONJUR.value

    # Get conjur_authn_login value
    result = runner.invoke(cli,
                           ['config', 'get', '--key', 'CONJUR_AUTHN_LOGIN'])
    assert result.exit_code == 0
    output = result.output.strip()
    key, value = output.split("=")
    assert key == "CONJUR_AUTHN_LOGIN"
    assert value == "user1"


def test_configure_get_nonexistent_key(runner, temp_config_home):
    # Try to get a key that does not exist
    result = runner.invoke(cli, ['config', 'get', '--key', 'NON_EXISTENT_KEY'])
    assert result.exit_code == 2
    assert "'--key': 'NON_EXISTENT_KEY' is not one of" in result.output


def test_config_list_command(runner, temp_config_home):
    """Test the config list command to display all configuration parameters."""
    # First set some configuration values
    runner.invoke(
        cli,
        ['config', 'set', '--provider', CredentialsProvider.FILE_DOTENV.value],
        input="\n"
    )

    # Run the list command
    result = runner.invoke(cli, ['config', 'list'])

    # Check that the command executed successfully
    assert result.exit_code == 0

    # Check that the output contains the expected configuration
    assert "Agent Guard Configuration:" in result.output
    assert f"{ConfigurationOptions.SECRET_PROVIDER.name}={CredentialsProvider.FILE_DOTENV.value}" in result.output


def test_secrets_set_and_get_commands(runner, temp_config_home, temp_secrets_dir):
    """Test setting and retrieving secrets using the CLI."""
    # First set the configuration to use the file provider (simplest for testing)
    runner.invoke(
        cli,
        ['config', 'set', '--provider', CredentialsProvider.FILE_DOTENV.value],
        input="\n"
    )

    secret_key = "test-secret"
    secret_value = "secret-value-123"
    namespace = os.path.join(temp_secrets_dir, "test-namespace")

    # Set a secret
    set_result = runner.invoke(
        cli,
        [
            'secrets', 'set',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', secret_key,
            '--secret_value', secret_value,
            '--namespace', namespace
        ]
    )

    # Check that the set command executed successfully
    assert set_result.exit_code == 0, f"Failed to set secret: {set_result.output}"

    # Get the secret
    get_result = runner.invoke(
        cli,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', secret_key,
            '--namespace', namespace
        ]
    )

    # Check that the get command executed successfully and returned the expected value
    assert get_result.exit_code == 0, f"Failed to get secret: {get_result.output}"
    assert secret_value in get_result.output


def test_secrets_get_nonexistent(runner, temp_config_home, temp_secrets_dir):
    """Test behavior when getting a nonexistent secret."""
    # Set up the configuration
    runner.invoke(
        cli,
        ['config', 'set', '--provider', CredentialsProvider.FILE_DOTENV.value],
        input="\n"
    )

    namespace = os.path.join(temp_secrets_dir, "nonexistent-namespace")

    # Try to get a secret that doesn't exist
    result = runner.invoke(
        cli,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', 'nonexistent-key',
            '--namespace', namespace
        ]
    )

    # The command might succeed but return an empty value, or fail with an error
    if result.exit_code == 0:
        # If it succeeds, the value should be empty or indicate not found
        assert result.output.strip() == "" or "not found" in result.output.lower()
    else:
        # If it fails, check for an error message
        assert "not found" in result.output.lower() or "failed to retrieve" in result.output.lower()


def test_store_and_get_secret(runner, temp_config_home, clean_environment, temp_secrets_dir):
    """Test storing and retrieving a secret through the CLI using the file provider"""
    # First configure the file provider
    result = runner.invoke(
        cli,
        ['config', 'set', '--provider', CredentialsProvider.FILE_DOTENV.value]
    )
    assert result.exit_code == 0, f"Failed to configure file provider: {result.output}"

    secret_key = "my_secret"
    secret_value = "secret_value_123"
    namespace = os.path.join(temp_secrets_dir, "test-secrets")

    # Store a secret
    result = runner.invoke(
        cli,
        [
            'secrets', 'set',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', secret_key,
            '--secret_value', secret_value,
            '--namespace', namespace
        ]
    )
    assert result.exit_code == 0, f"Failed to store secret: {result.output}"

    # Retrieve the secret
    result = runner.invoke(
        cli,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', secret_key,
            '--namespace', namespace
        ]
    )

    assert result.exit_code == 0, f"Failed to retrieve secret: {result.output}"
    assert secret_value in result.output