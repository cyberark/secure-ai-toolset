from unittest.mock import MagicMock

import pytest

from secure_ai_toolset.credentials.aws_secrets_manager_provider import AWSSecretsProvider


@pytest.fixture(params=[AWSSecretsProvider])
def provider(request):
    return MagicMock(spec=request.param)


def test_connect(provider):
    provider.connect.return_value = True
    try:
        result = provider.connect()
        assert result == True
        provider.connect.assert_called_once()
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_store(provider):
    try:
        provider.store("key", "secret")
        provider.store.assert_called_once_with("key", "secret")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_get(provider):
    provider.get.return_value = "secret"
    try:
        result = provider.get("key")
        assert result == "secret"
        provider.get.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_delete(provider):
    provider.delete.return_value = "deleted"
    try:
        result = provider.delete("key")
        assert result == "deleted"
        provider.delete.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


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
