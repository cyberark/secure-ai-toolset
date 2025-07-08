import json
from unittest.mock import MagicMock, patch

import pytest
import botocore.exceptions

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException, SecretNotFoundException


@pytest.fixture
def mock_client():
    """Create a mock AWS Secrets Manager client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def direct_provider(mock_client):
    """Create provider with direct secret access (no namespace)."""
    with patch("boto3.client", return_value=mock_client):
        provider = AWSSecretsProvider(region_name="us-west-2")
        provider.connect()
        return provider, mock_client


@pytest.fixture
def namespace_provider(mock_client):
    """Create provider with namespace-based secret access."""
    with patch("boto3.client", return_value=mock_client):
        provider = AWSSecretsProvider(region_name="us-west-2", namespace="test-namespace")
        provider.connect()
        return provider, mock_client


def test_connect():
    """Test connection to AWS Secrets Manager."""
    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        provider = AWSSecretsProvider(region_name="us-west-2")

        # First connection should create client
        result = provider.connect()
        assert result is True
        mock_boto_client.assert_called_once_with(service_name="secretsmanager", region_name="us-west-2")

        # Second connection should reuse client
        mock_boto_client.reset_mock()
        result = provider.connect()
        assert result is True
        mock_boto_client.assert_not_called()


def test_connect_failure():
    """Test connection failure handling."""
    with patch("boto3.client") as mock_boto_client:
        mock_boto_client.side_effect = Exception("Connection failed")
        provider = AWSSecretsProvider(region_name="us-west-2")

        with pytest.raises(SecretProviderException) as excinfo:
            provider.connect()
        assert "Error connecting to the secret provider" in str(excinfo.value)
        assert "Connection failed" in str(excinfo.value)


def test_get_direct(direct_provider):
    """Test getting secrets directly (no namespace)."""
    provider, mock_client = direct_provider

    # Setup mock response
    mock_response = {"ResponseMetadata": {"HTTPStatusCode": 200}, "SecretString": "test_value"}
    mock_client.get_secret_value.return_value = mock_response

    # Test getting a simple string secret
    result = provider.get("test_key")
    assert result == "test_value"
    mock_client.get_secret_value.assert_called_with(SecretId="test_key")


def test_get_namespace(namespace_provider):
    """Test getting secrets from a namespace collection."""
    provider, mock_client = namespace_provider

    # Setup mock response for namespace
    mock_response = {"ResponseMetadata": {"HTTPStatusCode": 200}, "SecretString": '{"key1": "value1", "key2": "value2"}'}
    mock_client.get_secret_value.return_value = mock_response

    # Test getting key1 from namespace
    result = provider.get("key1")
    assert result == "value1"
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")

    # Test getting key2 from namespace
    mock_client.reset_mock()
    mock_client.get_secret_value.return_value = mock_response
    result = provider.get("key2")
    assert result == "value2"
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")

    # Test getting non-existent key from namespace
    mock_client.reset_mock()
    mock_client.get_secret_value.return_value = mock_response
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get("key3")
    assert excinfo.value.key == "key3"
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")


def test_get_all_namespace_keys(namespace_provider):
    """Test getting all keys from a namespace."""
    provider, mock_client = namespace_provider

    # Setup mock response for namespace
    namespace_content = {"key1": "value1", "key2": "value2"}
    mock_response = {"ResponseMetadata": {"HTTPStatusCode": 200}, "SecretString": json.dumps(namespace_content)}
    mock_client.get_secret_value.return_value = mock_response

    # Test getting all keys from namespace
    result = provider.get()
    assert result == namespace_content
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")


def test_get_direct_not_found(direct_provider):
    """Test handling of resource not found errors."""
    provider, mock_client = direct_provider

    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, "exceptions"):
        mock_client.exceptions = MagicMock()

    # Create a proper ResourceNotFoundException
    error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Secret not found"}}
    exception = botocore.exceptions.ClientError(error_response, "get_secret_value")
    mock_client.exceptions.ResourceNotFoundException = exception.__class__

    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception

    # Resource not found should raise SecretNotFoundException
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get("test_key")
    assert excinfo.value.key == "test_key"
    mock_client.get_secret_value.assert_called_with(SecretId="test_key")


def test_get_namespace_not_found(namespace_provider):
    """Test getting a key when the namespace doesn't exist."""
    provider, mock_client = namespace_provider

    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, "exceptions"):
        mock_client.exceptions = MagicMock()

    # Create a proper ResourceNotFoundException
    error_response = {"Error": {"Code": "ResourceNotFoundException", "Message": "Secret not found"}}
    exception = botocore.exceptions.ClientError(error_response, "get_secret_value")
    mock_client.exceptions.ResourceNotFoundException = exception.__class__

    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception

    # Namespace not found should raise SecretNotFoundException
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get("test_key")
    assert excinfo.value.key == "test-namespace:test_key"
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")


def test_get_namespace_invalid_json(namespace_provider):
    """Test getting from a namespace with invalid JSON content."""
    provider, mock_client = namespace_provider

    # Setup mock response with invalid JSON
    mock_response = {"ResponseMetadata": {"HTTPStatusCode": 200}, "SecretString": "not valid json"}
    mock_client.get_secret_value.return_value = mock_response

    # Invalid JSON should raise SecretProviderException from _try_parse
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get("test_key")

    # Verify the exception message matches what we expect from _try_parse
    assert "Failed to parse JSON" in str(excinfo.value)

    # Should have tried to get the namespace
    mock_client.get_secret_value.assert_called_with(SecretId="test-namespace")


def test_get_invalid_status(direct_provider):
    """Test getting a secret with invalid HTTP status response."""
    provider, mock_client = direct_provider

    # Setup mock response with invalid status
    mock_response = {"ResponseMetadata": {"HTTPStatusCode": 400}, "SecretString": "test_value"}
    mock_client.get_secret_value.return_value = mock_response

    # Invalid status should raise SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get("test_key")
    assert "Error retrieving secret: test_key" in str(excinfo.value)


def test_get_missing_secret_string(direct_provider):
    """Test getting a secret with missing SecretString in response."""
    provider, mock_client = direct_provider

    # Setup mock response with missing SecretString
    mock_response = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
        # No SecretString
    }
    mock_client.get_secret_value.return_value = mock_response

    # Missing SecretString should raise SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get("test_key")
    assert "Error retrieving secret: test_key" in str(excinfo.value)
