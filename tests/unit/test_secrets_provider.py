import uuid
from unittest.mock import MagicMock

import pytest

from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


@pytest.fixture(params=[BaseSecretsProvider, AWSSecretsProvider])
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


def test_delete(provider):
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
    with pytest.raises(Exception) as excinfo:
        provider.delete("key")
    assert str(excinfo.value) == "Delete failed"
    provider.delete.assert_called_once_with("key")
