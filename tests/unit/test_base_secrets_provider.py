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
        self._get_calls = []
        self._storage = {}  # In-memory storage for testing
        
    def connect(self) -> bool:
        self._connect_called = True
        return True
        
    def _get(self, key: Optional[str] = None) -> Optional[Union[str, Dict[str, str]]]:
        self._get_calls.append(key)
        if key is None:
            # Return all secrets if key is None
            return dict(self._storage)
        return self._storage.get(key)


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


# Test the _try_parse method
def test_try_parse_none():
    """Test that _try_parse handles None input."""
    provider = TestSecretsProvider()
    
    with pytest.raises(SecretProviderException) as excinfo:
        provider._try_parse(None)
    
    assert "Raw secret is None" in str(excinfo.value)


def test_try_parse_string_json():
    """Test that _try_parse correctly parses JSON strings."""
    provider = TestSecretsProvider()
    
    result = provider._try_parse('{"key": "value"}')
    assert isinstance(result, dict)
    assert result == {"key": "value"}


def test_try_parse_string_invalid_json():
    """Test that _try_parse raises exception for invalid JSON strings."""
    provider = TestSecretsProvider()
    
    with pytest.raises(SecretProviderException) as excinfo:
        provider._try_parse('not valid json')
    
    assert "Failed to parse JSON" in str(excinfo.value)


def test_try_parse_dict():
    """Test that _try_parse passes through dictionaries."""
    provider = TestSecretsProvider()
    
    input_dict = {"key": "value"}
    result = provider._try_parse(input_dict)
    
    assert result is input_dict
    assert result == {"key": "value"}


def test_try_parse_invalid_type():
    """Test that _try_parse raises exception for invalid types."""
    provider = TestSecretsProvider()
    
    with pytest.raises(SecretProviderException) as excinfo:
        provider._try_parse(123)
    
    assert "Unexpected type for raw secret" in str(excinfo.value)