import pytest

from agent_guard_core.credentials.gcp_secrets_manager_provider import GCPSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture()
def provider(scope="module"):
    return GCPSecretsProvider()


@pytest.mark.gcp
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.gcp
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.gcp
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


@pytest.mark.gcp
def test_get_secret(provider):
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"


@pytest.mark.gcp
def test_store_secret_with_none_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store(None, "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.gcp
def test_store_secret_with_empty_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("", "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.gcp
def test_store_secret_with_none_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", None)
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.gcp
def test_store_secret_with_empty_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", "")
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.gcp
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.gcp
def test_store_and_update_secret(provider):
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"


@pytest.mark.gcp
def test_get_secret_dictionary(provider):
    # Store multiple secrets
    test_secrets = {"key1": "value1", "key2": "value2", "key3": "value3"}

    # Store each secret individually
    for key, value in test_secrets.items():
        provider.store(key, value)

    # Get all secrets as dictionary
    fetched_secrets = provider.get_secret_dictionary()

    # Verify all secrets are present
    for key, value in test_secrets.items():
        assert key in fetched_secrets
        assert fetched_secrets[key] == value

    # Clean up
    for key in test_secrets.keys():
        provider.delete(key)


@pytest.mark.gcp
def test_store_secret_dictionary(provider):
    test_secrets = {
        "dict_key1": "dict_value1",
        "dict_key2": "dict_value2",
        "dict_key3": "dict_value3"
    }

    # Store dictionary of secrets
    provider.store_secret_dictionary(test_secrets)

    # Verify each secret
    for key, value in test_secrets.items():
        fetched_value = provider.get(key)
        assert fetched_value == value

    # Clean up
    for key in test_secrets.keys():
        provider.delete(key)
