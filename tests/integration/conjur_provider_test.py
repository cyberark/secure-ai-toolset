import shutil
from pathlib import Path

import pytest

from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture()
def provider(scope="module"):
    # Backup the existing .env and copy .env.conjur to .env
    env_path = Path(".env")
    backup_path = Path(".env.backup")
    conjur_env_path = Path(".env.conjur")

    if env_path.exists():
        shutil.copy(env_path, backup_path)
    shutil.copy(conjur_env_path, env_path)

    provider_instance = ConjurSecretsProvider(namespace='data/test-toolset')

    yield provider_instance

    # Restore the backup after use
    if backup_path.exists():
        shutil.copy(backup_path, env_path)
        backup_path.unlink()
    else:
        env_path.unlink()


@pytest.mark.conjur
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.conjur
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.conjur
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


@pytest.mark.conjur
def test_get_secret(provider):
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"


@pytest.mark.conjur
def test_store_secret_with_none_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store(None, "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_empty_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("", "test_value")
        fetched_value = provider.get("")
        assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_none_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", None)
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.conjur
def test_store_secret_with_empty_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", "")
        fetched_value = provider.get("test_key")
        assert fetched_value is None


@pytest.mark.conjur
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.conjur
def test_store_and_update_secret(provider):
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"
