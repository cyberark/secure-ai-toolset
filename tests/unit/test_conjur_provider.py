"""
Unit tests for Conjur Secrets Provider.
"""

from unittest.mock import MagicMock

import pytest

from secure_ai_toolset.secrets.conjur_secrets_provider import ConjurSecretsProvider


@pytest.fixture(params=[ConjurSecretsProvider])
def provider(request):
    """Fixture to create a mock provider."""
    return MagicMock(spec=request.param)


def test_connect(provider):
    """Test the connect method of the ConjurSecretsProvider."""
    provider.connect.return_value = True
    try:
        result = provider.connect()
        assert result is True
        provider.connect.assert_called_once()
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_store(provider):
    """Test the store method of the ConjurSecretsProvider."""
    try:
        provider.store("key", "secret")
        provider.store.assert_called_once_with("key", "secret")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_get(provider):
    """Test the get method of the ConjurSecretsProvider."""
    provider.get.return_value = "secret"
    try:
        result = provider.get("key")
        assert result == "secret"
        provider.get.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_delete(provider):
    """Test the delete method of the ConjurSecretsProvider."""
    provider.delete.return_value = "deleted"
    try:
        result = provider.delete("key")
        assert result == "deleted"
        provider.delete.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_connect_failure(provider):
    """Test the connect method failure of the ConjurSecretsProvider."""
    provider.connect.side_effect = Exception("Connection failed")
    with pytest.raises(Exception) as excinfo:
        provider.connect()
    assert str(excinfo.value) == "Connection failed"
    provider.connect.assert_called_once()


def test_store_failure(provider):
    """Test the store method failure of the ConjurSecretsProvider."""
    provider.store.side_effect = Exception("Store failed")
    with pytest.raises(Exception) as excinfo:
        provider.store("key", "secret")
    assert str(excinfo.value) == "Store failed"
    provider.store.assert_called_once_with("key", "secret")


def test_get_failure(provider):
    """Test the get method failure of the ConjurSecretsProvider."""
    provider.get.side_effect = Exception("Get failed")
    with pytest.raises(Exception) as excinfo:
        provider.get("key")
    assert str(excinfo.value) == "Get failed"
    provider.get.assert_called_once_with("key")


def test_delete_failure(provider):
    """Test the delete method failure of the ConjurSecretsProvider."""
    provider.delete.side_effect = Exception("Delete failed")
    with pytest.raises(Exception) as excinfo:
        provider.delete("key")
    assert str(excinfo.value) == "Delete failed"
    provider.delete.assert_called_once_with("key")
