"""
Integration tests for AWSSecretsProvider.
"""

import pytest

from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import SecretProviderException


@pytest.fixture()
def provider(scope="module"):
    """Fixture to provide an instance of AWSSecretsProvider."""
    return AWSSecretsProvider()


@pytest.mark.aws
def test_provider_ctor(provider):
    """Test the constructor of AWSSecretsProvider."""
    assert provider is not None


@pytest.mark.aws
def test_provider_connect(provider):
    """Test the connect method of AWSSecretsProvider."""
    assert provider.connect() is True


@pytest.mark.aws
def test_store_secret(provider):
    """Test storing, retrieving, and deleting a secret."""
    key = "test_key"
    value = "test_value"

    # Store get and compare
    provider.store(key, value)
    fetched_value = provider.get(key)
    assert fetched_value == value

    # delete secret and check its none
    provider.delete(key)
    fetched_value = provider.get(key)
    assert not fetched_value


@pytest.mark.aws
def test_get_secret(provider):
    """Test retrieving a stored secret."""
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"


@pytest.mark.aws
def test_store_secret_with_none_key(provider):
    """Test storing a secret with a None key."""
    with pytest.raises(SecretProviderException):
        provider.store(None, "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_empty_key(provider):
    """Test storing a secret with an empty key."""
    with pytest.raises(SecretProviderException):
        provider.store("", "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_none_value(provider):
    """Test storing a secret with a None value."""
    with pytest.raises(SecretProviderException):
        provider.store("test_key", None)
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_empty_value(provider):
    """Test storing a secret with an empty value."""
    with pytest.raises(SecretProviderException):
        provider.store("test_key", "")
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.aws
def test_get_nonexistent_secret(provider):
    """Test retrieving a nonexistent secret."""
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.aws
def test_store_and_update_secret(provider):
    """Test storing and updating a secret."""
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"
