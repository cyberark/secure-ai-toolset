import pytest

from secure_ai_toolset.secrets.conjur_secrets_provider import ConjurSecretsProvider

@pytest.fixture()
def provider(scope="module"):
    return ConjurSecretsProvider()


def test_provider_ctor(provider):
    provider = ConjurSecretsProvider()
    assert provider is not None


@pytest.mark.conjur
def test_provider_ctor(provider: ConjurSecretsProvider):
    assert provider is not None


@pytest.mark.conjur
def test_authentication(provider: ConjurSecretsProvider):
    assert provider.connect() is not None


@pytest.mark.conjur
def test_store_secret(provider):
    key = "data/test-toolset/my-environment"
    value = "test_value"

    # Store get and compare
    provider.store(key, value)
    fetched_value = provider.get(key)
    assert fetched_value == value

    # delete secret and check its none
    provider.delete(key)
    fetched_value = provider.get(key)
    assert not fetched_value


@pytest.mark.conjur
def test_get_secret(provider):
    provider.store("data/test-toolset/my-environment-2", "another_test_value")
    fetched_value = provider.get("data/test-toolset/my-environment-2")
    assert fetched_value == "another_test_value"


@pytest.mark.conjur
def test_store_secret_with_none_key(provider):
    provider.store(None, "test_value")
    fetched_value = provider.get("")
    assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_empty_key(provider):
    provider.store("", "test_value")
    fetched_value = provider.get("")
    assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_none_value(provider):
    provider.store("data/test-toolset/my-environment", None)
    fetched_value = provider.get("data/test-toolset/my-environment")
    assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_empty_value(provider):
    provider.store("data/test-toolset/my-environment", "")
    fetched_value = provider.get("data/test-toolset/my-environment")
    assert fetched_value is None


@pytest.mark.conjur
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.conjur
def test_store_and_update_secret(provider):
    provider.store("data/test-toolset/my-environment", "initial_value")
    provider.store("data/test-toolset/my-environment", "updated_value")
    fetched_value = provider.get("data/test-toolset/my-environment")
    assert fetched_value == "updated_value"
