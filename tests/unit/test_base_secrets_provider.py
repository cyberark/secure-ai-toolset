import json
import uuid
from typing import Optional, Dict, Union
from unittest.mock import MagicMock, patch

import pytest

from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider, SecretProviderException, SecretNotFoundException


# Create a concrete test implementation of BaseSecretsProvider
class TestSecretsProvider(BaseSecretsProvider):
    """Test implementation of BaseSecretsProvider for testing base class functionality."""
    
    def __init__(self, namespace: Optional[str] = None, **kwargs):
        super().__init__(namespace, **kwargs)
        self._connect_called = False
        self._store_calls = []
        self._get_calls = []
        self._delete_calls = []
        self._storage = {}  # In-memory storage for testing
        
    def connect(self) -> bool:
        self._connect_called = True
        return True
        
    def _store(self, key: str, secret: str) -> None:
        self._store_calls.append((key, secret))
        self._storage[key] = secret
        
    def _get(self, key: Optional[str] = None) -> Optional[Union[str, Dict[str, str]]]:
        self._get_calls.append(key)
        if key is None:
            # Return all secrets if key is None
            return dict(self._storage)
        return self._storage.get(key)
        
    def delete(self, key: str) -> None:
        if not key:
            raise SecretProviderException("delete: key is missing")
            
        self._delete_calls.append(key)
        if key in self._storage:
            del self._storage[key]


# Fixtures
@pytest.fixture
def direct_provider():
    """Provider without namespace for direct secret access."""
    return TestSecretsProvider()
    
@pytest.fixture
def namespace_provider():
    """Provider with namespace for collection-based access."""
    return TestSecretsProvider(namespace="test-namespace")

@pytest.fixture
def populated_provider():
    """Provider pre-populated with multiple secrets."""
    provider = TestSecretsProvider()
    provider._storage = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    return provider

@pytest.fixture
def populated_namespace_provider():
    """Provider with namespace pre-populated with multiple secrets."""
    provider = TestSecretsProvider(namespace="test-namespace")
    provider._storage["test-namespace"] = json.dumps({
        "ns-key1": "ns-value1",
        "ns-key2": "ns-value2",
        "ns-key3": "ns-value3"
    })
    return provider


# Direct access tests (no namespace)
def test_direct_store(direct_provider):
    """Test storing a secret directly without namespace."""
    direct_provider.store("test-key", "test-value")
    
    # Verify _store was called with the correct arguments
    assert direct_provider._store_calls == [("test-key", "test-value")]
    
    # Verify the secret was stored
    assert direct_provider._storage["test-key"] == "test-value"
    

def test_direct_get(direct_provider):
    """Test getting a secret directly without namespace."""
    # Store a secret first
    direct_provider._storage["test-key"] = "test-value"
    
    # Get the secret
    result = direct_provider.get("test-key")
    
    # Verify _get was called with the correct arguments
    assert direct_provider._get_calls == ["test-key"]
    
    # Verify the result
    assert result == "test-value"


def test_direct_get_nonexistent(direct_provider):
    """Test getting a nonexistent secret directly."""
    # Try to get a nonexistent secret
    with pytest.raises(SecretNotFoundException) as excinfo:
        direct_provider.get("nonexistent-key")
        
    # Verify _get was called with the correct arguments
    assert direct_provider._get_calls == ["nonexistent-key"]
    
    # Verify the exception has the correct message
    assert "nonexistent-key" in str(excinfo.value)


def test_direct_delete(direct_provider):
    """Test deleting a secret directly without namespace."""
    # Store a secret first
    direct_provider._storage["test-key"] = "test-value"
    
    # Delete the secret
    direct_provider.delete("test-key")
    
    # Verify delete was called with the correct arguments
    assert direct_provider._delete_calls == ["test-key"]
    
    # Verify the secret was deleted
    assert "test-key" not in direct_provider._storage


def test_direct_delete_empty_key(direct_provider):
    """Test deleting with an empty key."""
    with pytest.raises(SecretProviderException) as excinfo:
        direct_provider.delete("")
        
    # Verify the exception has the correct message
    assert "key is missing" in str(excinfo.value)


# New tests for get() with no key parameter
def test_direct_get_all_secrets(populated_provider):
    """Test getting all secrets directly without namespace."""
    # Get all secrets
    result = populated_provider.get()
    
    # Verify _get was called with None
    assert populated_provider._get_calls == [None]
    
    # Verify the result contains all secrets
    assert isinstance(result, dict)
    assert len(result) == 3
    assert result["key1"] == "value1"
    assert result["key2"] == "value2"
    assert result["key3"] == "value3"


def test_direct_get_all_empty(direct_provider):
    """Test getting all secrets when there are none."""
    # Get all secrets from an empty provider
    result = direct_provider.get()
    
    # Verify the result is an empty dictionary
    assert isinstance(result, dict)
    assert len(result) == 0


def test_namespace_get_all_secrets(populated_namespace_provider):
    """Test getting all secrets from a namespace."""
    # Get all secrets in the namespace
    result = populated_namespace_provider.get()
    
    # Verify _get was called with the namespace
    assert populated_namespace_provider._get_calls == ["test-namespace"]
    
    # Verify the result contains all secrets in the namespace
    assert isinstance(result, dict)
    assert len(result) == 3
    assert result["ns-key1"] == "ns-value1"
    assert result["ns-key2"] == "ns-value2"
    assert result["ns-key3"] == "ns-value3"


def test_namespace_get_all_nonexistent(namespace_provider):
    """Test getting all secrets from a nonexistent namespace."""
    # Get all secrets from a nonexistent namespace should raise SecretNotFoundException
    with pytest.raises(SecretNotFoundException) as excinfo:
        namespace_provider.get()
    
    # Verify _get was called with the namespace
    assert namespace_provider._get_calls == ["test-namespace"]
    
    # Verify the exception has the correct message
    assert "test-namespace" in str(excinfo.value)


def test_namespace_get_all_invalid_json(namespace_provider):
    """Test getting all secrets from a namespace with invalid JSON."""
    # Set up an invalid JSON namespace
    namespace_provider._storage["test-namespace"] = "not valid json"
    
    # Get all secrets from the namespace - should raise SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        namespace_provider.get()
    
    # Verify _get was called with the namespace
    assert namespace_provider._get_calls == ["test-namespace"]
    
    # Verify the exception has the correct message
    assert "Failed to parse JSON" in str(excinfo.value)


def test_namespace_store_invalid_json(namespace_provider):
    """Test storing when the existing namespace content is invalid JSON."""
    # Set up an invalid JSON namespace
    namespace_provider._storage["test-namespace"] = "not valid json"
    
    # Store a secret - should raise SecretProviderException for invalid JSON
    with pytest.raises(SecretProviderException) as excinfo:
        namespace_provider.store("test-key", "test-value")
    
    # Verify _get was called but _store was not
    assert namespace_provider._get_calls == ["test-namespace"]
    assert len(namespace_provider._store_calls) == 0
    
    # Verify the exception has the correct message
    assert "Failed to parse JSON" in str(excinfo.value)


def test_namespace_get_invalid_json(namespace_provider):
    """Test getting from a namespace with invalid JSON content."""
    # Set up an invalid JSON namespace
    namespace_provider._storage["test-namespace"] = "not valid json"
    
    # Try to get a key - should raise SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        namespace_provider.get("test-key")
    
    # Verify _get was called with the namespace
    assert namespace_provider._get_calls == ["test-namespace"]
    
    # Verify the exception has the correct message
    assert "Failed to parse JSON" in str(excinfo.value)


# Namespace access tests
def test_namespace_store_new(namespace_provider):
    """Test storing a secret in a namespace when the namespace doesn't exist yet."""
    # Store a secret in the namespace
    namespace_provider.store("test-key", "test-value")
    
    # Verify _get and _store were called correctly
    assert namespace_provider._get_calls == ["test-namespace"]
    assert len(namespace_provider._store_calls) == 1
    assert namespace_provider._store_calls[0][0] == "test-namespace"
    
    # Verify the JSON structure
    stored_json = json.loads(namespace_provider._store_calls[0][1])
    assert stored_json == {"test-key": "test-value"}


def test_namespace_store_existing(namespace_provider):
    """Test storing a secret in an existing namespace."""
    # Set up an existing namespace collection
    namespace_provider._storage["test-namespace"] = json.dumps({
        "existing-key": "existing-value"
    })
    
    # Store a new secret in the namespace
    namespace_provider.store("test-key", "test-value")
    
    # Verify _get and _store were called correctly
    assert namespace_provider._get_calls == ["test-namespace"]
    assert len(namespace_provider._store_calls) == 1
    
    # Verify the JSON structure contains both keys
    stored_json = json.loads(namespace_provider._store_calls[0][1])
    assert stored_json == {
        "existing-key": "existing-value",
        "test-key": "test-value"
    }


def test_namespace_store_update(namespace_provider):
    """Test updating an existing secret in a namespace."""
    # Set up an existing namespace collection with the key
    namespace_provider._storage["test-namespace"] = json.dumps({
        "test-key": "old-value",
        "other-key": "other-value"
    })
    
    # Update the existing secret
    namespace_provider.store("test-key", "new-value")
    
    # Verify the JSON structure has the updated value
    stored_json = json.loads(namespace_provider._store_calls[0][1])
    assert stored_json == {
        "test-key": "new-value",
        "other-key": "other-value"
    }


def test_namespace_delete(namespace_provider):
    """Test deleting a key from a namespace via the delete method."""
    # This test depends on how delete is implemented in concrete classes
    # Since BaseSecretsProvider doesn't implement namespace-aware delete,
    # we'll just verify the delete method is called
    namespace_provider._storage["test-namespace"] = json.dumps({
        "test-key": "test-value", 
        "other-key": "other-value"
    })
    
    namespace_provider.delete("test-key")
    assert namespace_provider._delete_calls == ["test-key"]


# Abstract class verification
def test_abstract_class():
    """Verify BaseSecretsProvider is properly abstract."""
    # Creating an instance of the abstract class should fail
    with pytest.raises(TypeError):
        BaseSecretsProvider()


# Test error handling in _get_raw_secret
def test_get_raw_secret_exception_handling(direct_provider):
    """Test that _get_raw_secret properly handles exceptions from _get."""
    # Mock _get to raise an exception
    original_get = direct_provider._get
    
    def mock_get(key):
        if key == "error-key":
            raise ValueError("Test error")
        return original_get(key)
        
    direct_provider._get = mock_get
    
    # Should wrap the exception in a SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        direct_provider._get_raw_secret("error-key")
        
    assert "Error retrieving secret" in str(excinfo.value)
    assert "Test error" in str(excinfo.value)


# Test error handling in _get_raw_secret with no key
def test_get_raw_secret_all_exception_handling(direct_provider):
    """Test that _get_raw_secret properly handles exceptions from _get when getting all secrets."""
    # Mock _get to raise an exception when called with None
    original_get = direct_provider._get
    
    def mock_get(key):
        if key is None:
            raise ValueError("Test error for all secrets")
        return original_get(key)
        
    direct_provider._get = mock_get
    
    # Should wrap the exception in a SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        direct_provider._get_raw_secret(None)
        
    assert "Error retrieving all secrets" in str(excinfo.value)
    assert "Test error for all secrets" in str(excinfo.value)
