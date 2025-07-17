import os
import shutil
import tempfile
from pathlib import Path
import sys
import dotenv

import pytest
from click.testing import CliRunner

# Import the CLI module using an indirect approach to avoid side effects during test discovery
@pytest.fixture
def cli_module():
    from agent_guard_core.cli import cli
    # Return the actual Click command object, not the module
    return cli.cli

from agent_guard_core.credentials.enum import CredentialsProvider


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_secrets_dir():
    """Create a temporary directory for storing test secrets with pre-populated files"""
    # Create a temporary directory for secrets
    temp_dir = tempfile.mkdtemp()
    
    # Create pre-populated secrets for testing
    # 1. Create a directory for test namespace
    test_namespace = os.path.join(temp_dir, "test-namespace")
    os.makedirs(test_namespace, exist_ok=True)
    
    # 2. Create a .env file with test secrets
    env_path = os.path.join(test_namespace, ".env")
    with open(env_path, "w") as f:
        f.write("test-secret=secret-value-123\n")
        f.write("another-secret=another-value-456\n")
        f.write("API_TOKEN=my-special-token\n")
    
    # 3. Create another namespace for multiple secrets test
    multi_namespace = os.path.join(temp_dir, "multiple-secrets")
    os.makedirs(multi_namespace, exist_ok=True)
    
    # 4. Add multiple secrets to this namespace
    multi_env_path = os.path.join(multi_namespace, ".env")
    with open(multi_env_path, "w") as f:
        f.write("SECRET1=value1\n")
        f.write("SECRET2=value2\n")
        f.write("API_KEY=test-api-key\n")
        f.write("DATABASE_URL=postgres://user:password@localhost/db\n")
        f.write("DEBUG=true\n")
    
    # Debug: Print file contents to ensure they're correctly created
    with open(env_path) as f:
        content = f.read()
        print(f"Test namespace file content: {content}")
    
    with open(multi_env_path) as f:
        content = f.read()
        print(f"Multiple secrets file content: {content}")
        
    # Verify the files were created correctly
    assert os.path.exists(env_path), f"Test file not created: {env_path}"
    assert os.path.exists(multi_env_path), f"Multiple secrets file not created: {multi_env_path}"
    
    yield temp_dir
    
    # Clean up
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


def test_get_secret_from_dotenv(runner, temp_secrets_dir, cli_module):
    """Test retrieving a secret through the CLI using pre-populated dotenv file."""
    # Secret is already created in the temp_secrets_dir fixture
    secret_key = "test-secret"
    secret_value = "secret-value-123"
    namespace = os.path.join(temp_secrets_dir, "test-namespace")
    
    # Use absolute path to avoid any path resolution issues
    # Include the .env filename in the namespace path
    abs_namespace = os.path.abspath(os.path.join(namespace, ".env"))
    
    # Debug: Check namespace file exists
    assert os.path.exists(abs_namespace), f"Environment file doesn't exist: {abs_namespace}"
    
    # Test direct reading with dotenv to ensure it's working
    from dotenv import dotenv_values
    values = dotenv_values(abs_namespace)
    assert secret_key in values, f"Expected key {secret_key} in {values}"
    assert values[secret_key] == secret_value, f"Expected value {secret_value} for key {secret_key}, got {values.get(secret_key)}"

    # Get the secret using the CLI
    get_result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', secret_key,
            '--namespace', abs_namespace  # Use absolute path with .env file
        ]
    )

    # Debug output for failed tests
    if get_result.exit_code != 0:
        print(f"Command failed with exit code {get_result.exit_code}: {get_result.output}")
        if hasattr(get_result, 'exception'):
            print(f"Exception: {str(get_result.exception)}")
            import traceback
            traceback.print_exception(type(get_result.exception), get_result.exception, get_result.exception.__traceback__)

    # Check that the get command executed successfully and returned the expected value
    assert get_result.exit_code == 0, f"Failed to get secret: {get_result.output}"
    assert secret_value in get_result.output


def test_secrets_get_nonexistent(runner, temp_secrets_dir, cli_module):
    """Test behavior when getting a nonexistent secret."""
    namespace = os.path.join(temp_secrets_dir, "nonexistent-namespace")
    # Create the directory but don't add any secrets
    os.makedirs(namespace, exist_ok=True)
    
    # Include the .env file in the path even though it doesn't exist
    abs_namespace = os.path.abspath(os.path.join(namespace, ".env"))
    
    # Create an empty .env file to avoid file not found errors
    with open(abs_namespace, "w") as f:
        pass
    
    # Try to get a secret that doesn't exist
    result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', 'nonexistent-key',
            '--namespace', abs_namespace  # Use absolute path with .env file
        ]
    )

    # The command might succeed but return an empty value, or fail with an error
    if result.exit_code == 0:
        # If it succeeds, the value should be empty or indicate not found
        assert result.output.strip() == "" or "not found" in result.output.lower()
    else:
        # If it fails, check for an error message
        assert "not found" in result.exception.__str__().lower() or "failed to retrieve" in result.exception.__str__().lower()


def test_get_multiple_secrets(runner, temp_secrets_dir, cli_module):
    """Test retrieving multiple secrets from a pre-populated dotenv file."""
    # Secrets are already created in the temp_secrets_dir fixture
    namespace = os.path.join(temp_secrets_dir, "multiple-secrets")
    
    # Use absolute path to avoid any path resolution issues
    # Include the .env filename in the namespace path
    abs_namespace = os.path.abspath(os.path.join(namespace, ".env"))
    
    # Debug: Check if the file exists
    assert os.path.exists(abs_namespace), f"Environment file doesn't exist: {abs_namespace}"
    
    # Test direct reading with dotenv
    from dotenv import dotenv_values
    values = dotenv_values(abs_namespace)
    assert "API_KEY" in values, f"Expected key 'API_KEY' in {values}"
    assert values["API_KEY"] == "test-api-key", f"Expected value 'test-api-key', got {values.get('API_KEY')}"
    
    # Get one of the secrets
    result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', 'API_KEY',
            '--namespace', abs_namespace  # Use absolute path with .env file
        ]
    )

    # Debug info
    if result.exit_code != 0:
        print(f"Command failed with: {result.output}")
        if hasattr(result, 'exception'):
            print(f"Exception: {str(result.exception)}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)
    
    # Check results
    assert result.exit_code == 0, f"Failed to get secret: {result.output}"
    assert "test-api-key" in result.output, f"Expected 'test-api-key' in output but got: {result.output}"
    
    # Test another secret from the same file
    result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.FILE_DOTENV.value,
            '--secret_key', 'DATABASE_URL',
            '--namespace', abs_namespace  # Use absolute path with .env file
        ]
    )
    
    # Check results
    assert result.exit_code == 0, f"Failed to get secret: {result.output}"
    assert "postgres://user:password@localhost/db" in result.output


def test_get_with_aws_provider_options(runner, clean_environment, cli_module):
    """Test specifying AWS provider options with the get command."""
    # This test just verifies the command accepts AWS options
    # We're not actually connecting to AWS
    result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.AWS_SECRETS_MANAGER.value,
            '--secret_key', 'test-secret',
            '--aws-region', 'us-east-1',
            '--aws-access-key-id', 'test-access-key',
            '--aws-secret-access-key', 'test-secret-key'
        ]
    )
    
    # We expect failure since we're not actually connecting to AWS,
    # but not due to parameter issues
    assert "aws" not in result.output.lower() or "option" not in result.output.lower()


def test_get_with_gcp_provider_options(runner, clean_environment, cli_module):
    """Test specifying GCP provider options with the get command."""
    # This test just verifies the command accepts GCP options
    result = runner.invoke(
        cli_module,
        [
            'secrets', 'get',
            '--provider', CredentialsProvider.GCP_SECRETS_MANAGER.value,
            '--secret_key', 'test-secret',
            '--gcp-project-id', 'test-project',
            '--gcp-secret-id', 'test-secret-id',
            '--gcp-replication-type', 'automatic'
        ]
    )
    
    # We expect failure since we're not actually connecting to GCP,
    # but not due to parameter issues
    assert "gcp" not in result.output.lower() or "option" not in result.output.lower()