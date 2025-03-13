from typing import List
import pytest
from secure_ai_toolset.secrets.aws_secrets_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.conjur_secrets_provider import ConjurSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider

secret_providers = [AWSSecretsProvider()]
# secret_providers = [AWSSecretsProvider(), ConjurSecretsProvider()]

@pytest.mark.parametrize("provider", secret_providers)
def test_provider_ctor(provider: BaseSecretsProvider):
    assert provider is not None

@pytest.mark.parametrize("provider", secret_providers)
def test_store_secret(provider):
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


@pytest.mark.parametrize("provider", secret_providers)
def test_get_secret(provider):
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"

@pytest.mark.parametrize("provider", secret_providers)
def test_store_secret_with_none_key(provider):
    provider.store(None, "test_value")
    fetched_value = provider.get("")
    assert fetched_value is None

@pytest.mark.parametrize("provider", secret_providers)
def test_store_secret_with_empty_key(provider):
    provider.store("", "test_value")
    fetched_value = provider.get("")
    assert fetched_value is None

@pytest.mark.parametrize("provider", secret_providers)
def test_store_secret_with_none_value(provider):
    provider.store("test_key", None)
    fetched_value = provider.get("test_key")
    assert fetched_value is None

@pytest.mark.parametrize("provider", secret_providers)
def test_store_secret_with_empty_value(provider):
    provider.store("test_key", "")
    fetched_value = provider.get("test_key")
    assert fetched_value is None

@pytest.mark.parametrize("provider", secret_providers)
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None

@pytest.mark.parametrize("provider", secret_providers)
def test_store_and_update_secret(provider):
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"
