import os
import tempfile
import shutil
from pathlib import Path
import pytest

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider, SecretProviderException


@pytest.fixture(scope="module")
def temp_dir():
    """Create a temporary directory for secret files during tests"""
    # Create a temporary directory
    test_dir = tempfile.mkdtemp()
    
    # Save the current working directory
    original_dir = os.getcwd()
    
    # Change to the temporary directory
    os.chdir(test_dir)
    
    yield test_dir
    
    # Clean up: Change back to original directory and remove temp directory
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


@pytest.fixture(scope="module")
def secret_provider(temp_dir) -> BaseSecretsProvider:
    return FileSecretsProvider(namespace=os.path.join(temp_dir, "teststest_secrets"))


@pytest.fixture(scope="module")
def secret_provider_with_directory(temp_dir) -> BaseSecretsProvider:
    # Create data directory if it doesn't exist
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    return FileSecretsProvider(namespace=os.path.join(data_dir, "test_secrets"))


@pytest.fixture(scope="module")
def secret_provider_with_multiple_directories(temp_dir) -> BaseSecretsProvider:
    # Create nested directory structure
    nested_dir = os.path.join(temp_dir, "data", "multiple", "directories")
    os.makedirs(nested_dir, exist_ok=True)
    
    return FileSecretsProvider(namespace=os.path.join(nested_dir, "test_secrets"))


def test_connect(secret_provider):
    assert secret_provider
    assert secret_provider.connect() is True


def test_get_nonexistent_secret(secret_provider):
    secret_key = 'secret1'
    secret_provider.delete(secret_key)
    secret = secret_provider.get(secret_key)
    assert secret is None


def test_create_get_nonexistent_secret(secret_provider):
    secret_key = 'key1'
    secret_provider.delete(secret_key)
    secret_value = 'value1'
    # Create secret, write and compare after get
    secret_provider.store(secret_key, secret_value)
    fetched_secret = secret_provider.get(secret_key)
    assert fetched_secret == secret_value

    # delete the secret and validate its empty
    secret_provider.delete(secret_key)
    fetched_secret = secret_provider.get(secret_key)
    assert fetched_secret is None


@pytest.mark.parametrize("key", ["", None])
def test_delete_secret_none_empty(secret_provider, key):
    with pytest.raises(SecretProviderException) as e:
        result = secret_provider.delete(key)
        assert result is None


def test_namespace_with_directory(secret_provider_with_directory):
    secret_key = 'dir_key'
    secret_value = 'dir_value'
    secret_provider_with_directory.delete(secret_key)

    # Create secret, write and compare after get
    secret_provider_with_directory.store(secret_key, secret_value)
    fetched_secret = secret_provider_with_directory.get(secret_key)
    assert fetched_secret == secret_value

    # delete the secret and validate its empty
    secret_provider_with_directory.delete(secret_key)
    fetched_secret = secret_provider_with_directory.get(secret_key)
    assert fetched_secret is None


def test_namespace_with_multiple_directories(
        secret_provider_with_multiple_directories):
    secret_key = 'multi_dir_key'
    secret_value = 'multi_dir_value'
    secret_provider_with_multiple_directories.delete(secret_key)

    # Create secret, write and compare after get
    secret_provider_with_multiple_directories.store(secret_key, secret_value)
    fetched_secret = secret_provider_with_multiple_directories.get(secret_key)
    assert fetched_secret == secret_value

    # delete the secret and validate its empty
    secret_provider_with_multiple_directories.delete(secret_key)
    fetched_secret = secret_provider_with_multiple_directories.get(secret_key)
    assert fetched_secret is None
