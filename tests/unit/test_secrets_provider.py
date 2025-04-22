import uuid
from unittest.mock import MagicMock

import pytest

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture(params=[AWSSecretsProvider, FileSecretsProvider])
def provider(request):
    return MagicMock(spec=request.param)


def test_connect(provider):
    provider.connect.return_value = "connected"
    result = provider.connect()
    assert result == "connected"
    provider.connect.assert_called_once()


def test_store(provider):
    provider.store("key", "secret")
    provider.store.assert_called_once_with("key", "secret")


def test_get(provider):
    secret_value = uuid.uuid4()
    provider.get.return_value = secret_value
    result = provider.get("key")
    assert result == secret_value
    provider.get.assert_called_once_with("key")


def test_delete_secret(provider):
    provider.delete.return_value = None
    result = provider.delete("key")
    assert result is None
    provider.delete.assert_called_once_with("key")


def test_connect_failure(provider):
    provider.connect.side_effect = Exception("Connection failed")
    with pytest.raises(Exception) as excinfo:
        provider.connect()
    assert str(excinfo.value) == "Connection failed"
    provider.connect.assert_called_once()


def test_store_failure(provider):
    provider.store.side_effect = Exception("Store failed")
    with pytest.raises(Exception) as excinfo:
        provider.store("key", "secret")
    assert str(excinfo.value) == "Store failed"
    provider.store.assert_called_once_with("key", "secret")


def test_get_failure(provider):
    provider.get.side_effect = Exception("Get failed")
    with pytest.raises(Exception) as excinfo:
        provider.get("key")
    assert str(excinfo.value) == "Get failed"
    provider.get.assert_called_once_with("key")


def test_delete_failure(provider):
    provider.delete.side_effect = Exception("Delete failed")
    with pytest.raises(Exception) as e:
        provider.delete("key")
    assert str(e.value) == "Delete failed"
    provider.delete.assert_called_once_with("key")


@pytest.mark.parametrize("key", ["", None])
def test_delete_secret_none_empty(provider, key):
    provider.delete.return_value = None
    provider.delete.side_effect = SecretProviderException("delete failed")
    with pytest.raises(SecretProviderException) as e:
        result = provider.delete(key)
        assert result is None
        provider.delete.assert_called_once_with(key)
