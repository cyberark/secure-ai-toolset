import json
from unittest.mock import MagicMock, patch, call

import pytest
import boto3
import botocore.exceptions

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


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
        mock_boto_client.assert_called_once_with('secretsmanager', region_name='us-west-2')
        
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
    
    # Setup mock response with JSON
    mock_client.reset_mock()
    mock_response['SecretString'] = '{"key1": "value1", "key2": "value2"}'
    mock_client.get_secret_value.return_value = mock_response
    
    # Test getting a JSON secret
    result = provider.get('test_key')
    assert result == {"key1": "value1", "key2": "value2"}
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
    result = provider.get('key2')
    assert result == 'value2'
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # Test getting non-existent key from namespace
    result = provider.get('key3')
    assert result is None
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')


def test_get_errors():
    """Test error handling in get method."""
    provider = AWSSecretsProvider()
    
    # Test empty key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get('')
    assert "key is missing" in str(excinfo.value)
    
    # Test None key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.get(None)
    assert "key is missing" in str(excinfo.value)


def test_get_resource_not_found(direct_provider):
    """Test handling of resource not found errors."""
    provider, mock_client = direct_provider
    
    # Setup mock to raise ResourceNotFoundException
    error_response = {'Error': {'Code': 'ResourceNotFoundException'}}
    mock_client.exceptions.ResourceNotFoundException = boto3.client('secretsmanager').exceptions.ResourceNotFoundException
    mock_client.get_secret_value.side_effect = mock_client.exceptions.ResourceNotFoundException(error_response, 'get_secret_value')
    
    # Resource not found should return None
    result = provider.get('test_key')
    assert result is None
    mock_client.get_secret_value.assert_called_with(SecretId='test_key')


def test_store_direct(direct_provider):
    """Test storing secrets directly (no namespace)."""
    provider, mock_client = direct_provider
    
    # Test storing string value - new secret
    provider.store('test_key', 'test_value')
    mock_client.create_secret.assert_called_with(Name='test_key', SecretString='test_value')
    
    # Test storing string value - existing secret
    mock_client.reset_mock()
    mock_client.exceptions.ResourceExistsException = boto3.client('secretsmanager').exceptions.ResourceExistsException
    mock_client.create_secret.side_effect = mock_client.exceptions.ResourceExistsException({}, 'operation')
    provider.store('test_key', 'test_value')
    mock_client.put_secret_value.assert_called_with(SecretId='test_key', SecretString='test_value')
    
    # Test storing dictionary value
    mock_client.reset_mock()
    mock_client.create_secret.side_effect = None
    test_dict = {"nested": {"value": 123}, "list": [1, 2, 3]}
    provider.store('test_dict', test_dict)
    mock_client.create_secret.assert_called_with(Name='test_dict', SecretString=json.dumps(test_dict))


def test_store_namespace(namespace_provider):
    """Test storing secrets in a namespace collection."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for initial namespace get
    mock_client.get_secret_value.return_value = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': '{"existing": "old_value"}'
    }
    
    # Test storing new key in namespace
    provider.store('new_key', 'new_value')
    
    # Should have retrieved existing namespace content
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
    
    mock_client.reset_mock()
    mock_client.get_secret_value.return_value = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': json.dumps(expected_data)
    }
    mock_client.exceptions.ResourceExistsException = boto3.client('secretsmanager').exceptions.ResourceExistsException
    mock_client.create_secret.side_effect = mock_client.exceptions.ResourceExistsException({}, 'operation')
    
    provider.store('existing', 'new_existing_value')
    provider.store('existing', 'new_existing_value')
    
    expected_updated_data = {
        'existing': 'new_existing_value',
        'new_key': 'new_value'
    }
    mock_client.put_secret_value.assert_called_with(
        SecretId='test-namespace',
        SecretString=json.dumps(expected_updated_data)
    )


def test_store_namespace_creation(namespace_provider):
    """Test storing when namespace doesn't exist yet."""
    # Get provider and mock client from the fixture
    provider, mock_client = namespace_provider
    # Setup mock to simulate namespace not existing yet
    mock_client.exceptions.ResourceNotFoundException = boto3.client('secretsmanager').exceptions.ResourceNotFoundException
    mock_client.get_secret_value.side_effect = mock_client.exceptions.ResourceNotFoundException(
        {'Error': {'Code': 'ResourceNotFoundException'}}, 'get_secret_value')
    
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


def test_store_errors():
    """Test error handling in store method."""
    provider = AWSSecretsProvider()
    
    # Test empty key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.store('', 'value')
    assert "key or secret is missing" in str(excinfo.value)
    
    # Test None key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.store(None, 'value')
    assert "key or secret is missing" in str(excinfo.value)
    
    # Test None value
    with pytest.raises(SecretProviderException) as excinfo:
        provider.store('key', None)
    assert "key or secret is missing" in str(excinfo.value)


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
    mock_client.exceptions.ResourceNotFoundException = boto3.client('secretsmanager').exceptions.ResourceNotFoundException
    mock_client.delete_secret.side_effect = mock_client.exceptions.ResourceNotFoundException(
        {'Error': {'Code': 'ResourceNotFoundException'}}, 'delete_secret')
    
    # Should not raise an exception
    provider.delete('nonexistent_key')
    mock_client.delete_secret.assert_called_with(
        SecretId='nonexistent_key', 
        ForceDeleteWithoutRecovery=True
    )


def test_delete_namespace(namespace_provider):
    """Test deleting secrets from a namespace collection."""
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
    
    # Test deleting a non-existent key from namespace
    mock_client.reset_mock()
    provider.delete('nonexistent_key')
    
    # Should have checked namespace but not updated it
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    mock_client.put_secret_value.assert_not_called()


def test_delete_errors():
    """Test error handling in delete method."""
    provider = AWSSecretsProvider()
    
    # Test empty key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.delete('')
    assert "key is missing" in str(excinfo.value)
    
    # Test None key
    with pytest.raises(SecretProviderException) as excinfo:
        provider.delete(None)
    assert "key is missing" in str(excinfo.value)


def test_delete_namespace_invalid_json(namespace_provider):
    """Test deleting when namespace contains invalid JSON."""
    provider, mock_client = namespace_provider
    
    # Setup mock response for namespace with invalid JSON
    mock_response = {
        'ResponseMetadata': {'HTTPStatusCode': 200},
        'SecretString': 'not-valid-json'
    }
    mock_client.get_secret_value.return_value = mock_response
    
    # Delete should not raise an exception
    provider.delete('any_key')
    
    # Should have gotten namespace content
    mock_client.get_secret_value.assert_called_with(SecretId='test-namespace')
    
    # No update should occur with invalid JSON
    mock_client.put_secret_value.assert_not_called()
