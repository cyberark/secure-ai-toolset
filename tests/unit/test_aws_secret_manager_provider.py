import json
from unittest.mock import MagicMock, patch, call

import pytest
import boto3
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
    with patch('boto3.client', return_value=mock_client):
        provider = AWSSecretsProvider(region_name='us-west-2')
        provider.connect()
        return provider, mock_client


@pytest.fixture
def namespace_provider(mock_client):
    """Create provider with namespace-based secret access."""
    with patch('boto3.client', return_value=mock_client):
        provider = AWSSecretsProvider(region_name='us-west-2', namespace='test-namespace')
        provider.connect()
        return provider, mock_client


def test_connect():
    """Test connection to AWS Secrets Manager."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.return_value = MagicMock()
        provider = AWSSecretsProvider(region_name='us-west-2')
        
        # First connection should create client
        result = provider.connect()
        assert result is True
        mock_boto_client.assert_called_once_with(service_name='secretsmanager', region_name='us-west-2')
        
        # Second connection should reuse client
        mock_boto_client.reset_mock()
        result = provider.connect()
        assert result is True
        mock_boto_client.assert_not_called()


def test_connect_failure():
    """Test connection failure handling."""
    with patch('boto3.client') as mock_boto_client:
        mock_boto_client.side_effect = Exception("Connection failed")
        provider = AWSSecretsProvider(region_name='us-west-2')
        
        with pytest.raises(SecretProviderException) as excinfo:
            provider.connect()
        assert "Error connecting to the secret provider" in str(excinfo.value)
        assert "Connection failed" in str(excinfo.value)


def test_get_direct(direct_provider):
    """Test getting secrets directly (no namespace)."""
    provider, mock_client = direct_provider
    
    # Setup mock response
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': 'test_value'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Test getting a simple string secret
    result = provider.get('test_key')
    assert result == 'test_value'
    mock_client.get_secret_value.assert_called_with(SecretId='test_key')


def test_get_namespace(namespace_provider):
    """Test getting secrets from a namespace collection."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for namespace
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"key1": "value1", "key2": "value2"}'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Test getting key1 from namespace
    result = provider.get('key1')
    assert result == 'value1'
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Test getting key2 from namespace
    mock_client.reset_mock()
    mock_client.get_secret_value.return_value = mock_response
    result = provider.get('key2')
    assert result == 'value2'
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Test getting non-existent key from namespace
    mock_client.reset_mock()
    mock_client.get_secret_value.return_value = mock_response
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get('key3')
    assert excinfo.value.key == 'key3'
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')


def test_get_direct_not_found(direct_provider):
    """Test handling of resource not found errors."""
    provider, mock_client = direct_provider
    
    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}}
    exception = botocore.exceptions.ClientError(error_response, 'get_secret_value')
    mock_client.exceptions.ResourceNotFoundException = exception.__class__
    
    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception
    
    # Resource not found should raise SecretNotFoundException
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get('test_key')
    assert excinfo.value.key == 'test_key:test_key'
    mock_client.get_secret_value.assert_called_with(SecretId='test_key')


def test_get_namespace_not_found(namespace_provider):
    """Test getting a key when the namespace doesn't exist."""
    provider, mock_client = namespace_provider
    
    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}}
    exception = botocore.exceptions.ClientError(error_response, 'get_secret_value')
    mock_client.exceptions.ResourceNotFoundException = exception.__class__
    
    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception
    
    # Namespace not found should raise SecretNotFoundException
    with pytest.raises(SecretNotFoundException) as excinfo:
        provider.get('test_key')
    assert excinfo.value.key == 'test-namespace:test_key'
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')


def test_get_namespace_invalid_json(namespace_provider):
    """Test getting from a namespace with invalid JSON content."""
    provider, mock_client = namespace_provider
    
    # Setup mock response with invalid JSON
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': 'not valid json'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Invalid JSON should raise SecretProviderException from _try_parse
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get('test_key')
    
    # Verify the exception message matches what we expect from _try_parse
    assert "Failed to parse JSON" in str(excinfo.value)
    
    # Should have tried to get the namespace
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')


def test_store_direct(direct_provider):
    """Test storing secrets directly (no namespace)."""
    provider, mock_client = direct_provider
    
    # Test storing string value - new secret
    provider.store('test_key', 'test_value')
    mock_client.create_secret.assert_called_with(Name='test_key', SecretString='test_value')
    
    # Test storing string value - existing secret
    mock_client.reset_mock()
    
    # Setup mock to raise ResourceExistsException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceExistsException
    error_response = {'Error': {'Code': 'ResourceExistsException', 'Message': 'Secret already exists'}}
    exception = botocore.exceptions.ClientError(error_response, 'create_secret')
    mock_client.exceptions.ResourceExistsException = exception.__class__
    
    # Set the side effect for create_secret
    mock_client.create_secret.side_effect = exception
    
    provider.store('test_key', 'test_value')
    mock_client.put_secret_value.assert_called_with(SecretId='test_key', SecretString='test_value')


def test_store_namespace_new(namespace_provider):
    """Test storing when namespace doesn't exist yet."""
    provider, mock_client = namespace_provider
    
    # Setup mock to simulate namespace not existing yet
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}}
    exception = botocore.exceptions.ClientError(error_response, 'get_secret_value')
    mock_client.exceptions.ResourceNotFoundException = exception.__class__
    
    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception
    
    # Store a new key
    provider.store('first_key', 'first_value')
    
    # Should try to get namespace first
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Should create namespace with the key
    expected_data = {'first_key': 'first_value'}
    mock_client.create_secret.assert_called_with(
        Name='test-namespace',
        SecretString=json.dumps(expected_data)
    )


def test_store_namespace_existing(namespace_provider):
    """Test storing in an existing namespace."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for existing namespace
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"existing": "old_value"}'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Add a new key to namespace
    provider.store('new_key', 'new_value')
    
    # Should have gotten namespace content
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Should have stored updated namespace content
    expected_data = {
        'existing': 'old_value',
        'new_key': 'new_value'
    }
    mock_client.create_secret.assert_called_with(
        Name='test-namespace', 
        SecretString=json.dumps(expected_data)
    )


def test_store_namespace_update(namespace_provider):
    """Test updating an existing key in a namespace."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for existing namespace with key
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"existing": "old_value", "other": "value"}'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Update existing key in namespace
    provider.store('existing', 'new_value')
    
    # Should have gotten namespace content
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Should have stored updated namespace content
    expected_data = {
        'existing': 'new_value',
        'other': 'value'
    }
    mock_client.create_secret.assert_called_with(
        Name='test-namespace', 
        SecretString=json.dumps(expected_data)
    )


def test_store_namespace_invalid_json(namespace_provider):
    """Test storing when namespace exists with invalid JSON."""
    provider, mock_client = namespace_provider
    
    # Setup mock response with invalid JSON
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': 'not valid json'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Storing with invalid JSON in namespace should raise SecretProviderException
    with pytest.raises(SecretProviderException) as excinfo:
        provider.store('test_key', 'test_value')
    
    # Verify the exception message matches what we expect from _try_parse
    assert "Failed to parse JSON" in str(excinfo.value)
    
    # Should have gotten namespace content but not tried to update it
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.create_secret.assert_not_called()
    mock_client.put_secret_value.assert_not_called()


def test_delete_direct(direct_provider):
    """Test deleting secrets directly (no namespace)."""
    provider, mock_client = direct_provider
    
    # Test deleting a secret
    provider.delete('test_key')
    mock_client.delete_secret.assert_called_with(
        SecretId='test_key', 
        ForceDeleteWithoutRecovery=True
    )
    
    # Test deleting a non-existent secret
    mock_client.reset_mock()
    
    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}}
    exception = botocore.exceptions.ClientError(error_response, 'delete_secret')
    mock_client.exceptions.ResourceNotFoundException = exception.__class__
    
    # Set the side effect for delete_secret
    mock_client.delete_secret.side_effect = exception
    
    # Should not raise an exception
    provider.delete('nonexistent_key')
    mock_client.delete_secret.assert_called_with(
        SecretId='nonexistent_key', 
        ForceDeleteWithoutRecovery=True
    )


def test_delete_namespace_key(namespace_provider):
    """Test deleting a key from a namespace."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for namespace
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"key1": "value1", "key2": "value2", "key3": "value3"}'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Delete key2 from namespace
    provider.delete('key2')
    
    # Should have gotten namespace content
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Should have updated namespace without key2
    expected_updated_data = {
        'key1': 'value1',
        'key3': 'value3'
    }
    mock_client.put_secret_value.assert_called_with(
        SecretId='test-namespace',
        SecretString=json.dumps(expected_updated_data)
    )


def test_delete_namespace_nonexistent_key(namespace_provider):
    """Test deleting a non-existent key from a namespace."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for namespace
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"key1": "value1", "key3": "value3"}'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Delete non-existent key from namespace
    provider.delete('key2')
    
    # Should have checked namespace but not updated it
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.put_secret_value.assert_not_called()
    mock_client.delete_secret.assert_not_called()


def test_delete_namespace_not_found(namespace_provider):
    """Test deleting a key when the namespace doesn't exist."""
    provider, mock_client = namespace_provider
    
    # Setup mock to raise ResourceNotFoundException
    # Create exceptions attribute if it doesn't exist
    if not hasattr(mock_client, 'exceptions'):
        mock_client.exceptions = MagicMock()
    
    # Create a proper ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}}
    exception = botocore.exceptions.ClientError(error_response, 'get_secret_value')
    mock_client.exceptions.ResourceNotFoundException = exception.__class__
    
    # Set the side effect for get_secret_value
    mock_client.get_secret_value.side_effect = exception
    
    # Deleting from non-existent namespace should not raise error
    provider.delete('test_key')
    
    # Should have tried to get namespace
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.put_secret_value.assert_not_called()
    mock_client.delete_secret.assert_not_called()


def test_delete_namespace_invalid_json(namespace_provider):
    """Test deleting when namespace contains invalid JSON."""
    provider, mock_client = namespace_provider
    
    # Setup mock response with invalid JSON
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': 'not-valid-json'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Delete should not raise an exception with invalid JSON
    provider.delete('any_key')
    
    # Should have gotten namespace content but not updated it
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.put_secret_value.assert_not_called()
    mock_client.delete_secret.assert_not_called()


def test_delete_namespace_non_dict(namespace_provider):
    """Test deleting when namespace contains non-dictionary JSON."""
    provider, mock_client = namespace_provider
    
    # Setup mock response with JSON array
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '[1, 2, 3]'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Delete should not raise an exception with non-dictionary JSON
    provider.delete('any_key')
    
    # Should have gotten namespace content but not updated it
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.put_secret_value.assert_not_called()
    mock_client.delete_secret.assert_not_called()


def test_delete_empty_key(direct_provider):
    """Test deleting with an empty key."""
    provider, mock_client = direct_provider
    
    # Test empty key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.delete('')
    assert "key is missing" in str(excinfo.value)
    mock_client.delete_secret.assert_not_called()
