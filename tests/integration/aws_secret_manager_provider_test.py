import pytest

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture()
def provider(scope="module"):
    return AWSSecretsProvider()


@pytest.mark.aws
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.aws
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.aws
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


@pytest.mark.aws
def test_get_secret(provider):
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"


@pytest.mark.aws
def test_store_secret_with_none_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store(None, "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_empty_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("", "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_none_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", None)
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.aws
def test_store_secret_with_empty_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", "")
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.aws
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.aws
def test_store_and_update_secret(provider):
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"
