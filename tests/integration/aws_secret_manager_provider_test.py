import json
import os
import pytest

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture(scope="module")
def provider():
    """
    Creates real AWS secrets provider instance for integration testing.
    Tests will be skipped if AWS credentials aren't available.
    """
    # Check for AWS credentials
    if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
        pytest.skip("AWS credentials not available in environment")
    
    provider = AWSSecretsProvider()
    
    # Test the connection works before continuing
    try:
        if not provider.connect():
            pytest.skip("Could not connect to AWS Secrets Manager")
    except Exception as e:
        pytest.skip(f"Error connecting to AWS: {str(e)}")
    
    yield provider


@pytest.fixture(scope="module")
def namespace_provider():
    """
    Creates AWS secrets provider with namespace for integration testing.
    Tests will be skipped if AWS credentials aren't available.
    """
    # Check for AWS credentials
    if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
        pytest.skip("AWS credentials not available in environment")
    
    provider = AWSSecretsProvider(namespace="test-namespace")
    
    # Test the connection works before continuing
    try:
        if not provider.connect():
            pytest.skip("Could not connect to AWS Secrets Manager")
    except Exception as e:
        pytest.skip(f"Error connecting to AWS: {str(e)}")
    
    # Clean up the namespace before tests
    try:
        response = provider._client.get_secret_value(SecretId="test-namespace")
        provider._client.delete_secret(SecretId="test-namespace", ForceDeleteWithoutRecovery=True)
    except provider._client.exceptions.ResourceNotFoundException:
        pass
    
    yield provider
    
    # Clean up after tests
    try:
        provider._client.delete_secret(SecretId="test-namespace", ForceDeleteWithoutRecovery=True)
    except provider._client.exceptions.ResourceNotFoundException:
        pass


@pytest.mark.aws
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.aws
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.aws
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


@pytest.mark.aws
def test_get_secret(provider):
    provider.store("another_test_key", "another_test_value")
    fetched_value = provider.get("another_test_key")
    assert fetched_value == "another_test_value"
    
    # Clean up
    provider.delete("another_test_key")


@pytest.mark.aws
def test_store_secret_with_none_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store(None, "test_value")
    assert "key or secret is missing" in str(e.value)


@pytest.mark.aws
def test_store_secret_with_empty_key(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("", "test_value")
    assert "key or secret is missing" in str(e.value)


@pytest.mark.aws
def test_store_secret_with_none_value(provider):
    with pytest.raises(SecretProviderException) as e:
        provider.store("test_key", None)
    assert "key or secret is missing" in str(e.value)


@pytest.mark.aws
def test_get_nonexistent_secret(provider):
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.aws
def test_store_and_update_secret(provider):
    provider.store("update_test_key", "initial_value")
    provider.store("update_test_key", "updated_value")
    fetched_value = provider.get("update_test_key")
    assert fetched_value == "updated_value"
    
    # Clean up
    provider.delete("update_test_key")


@pytest.mark.aws
def test_store_dictionary_secret(provider):
    test_dict = {"key1": "value1", "key2": "value2"}
    provider.store("dict_test_key", test_dict)
    fetched_value = provider.get("dict_test_key")
    assert fetched_value == test_dict
    
    # Clean up
    provider.delete("dict_test_key")


# Namespace-specific tests
@pytest.mark.aws
def test_namespace_provider_ctor(namespace_provider):
    assert namespace_provider is not None
    assert namespace_provider._namespace == "test-namespace"


@pytest.mark.aws
def test_namespace_store_secret(namespace_provider):
    key = "ns_test_key"
    value = "test_value"

    # Store get and compare
    namespace_provider.store(key, value)
    fetched_value = namespace_provider.get(key)
    assert fetched_value == value
    
    # Check directly that the value is stored in the namespace
    response = namespace_provider._client.get_secret_value(SecretId="test-namespace")
    secrets_dict = json.loads(response["SecretString"])
    assert key in secrets_dict
    assert secrets_dict[key] == value
    
    # Delete and verify
    namespace_provider.delete(key)
    fetched_value = namespace_provider.get(key)
    assert fetched_value is None


@pytest.mark.aws
def test_namespace_multiple_secrets(namespace_provider):
    # Store multiple secrets in the same namespace
    namespace_provider.store("key1", "value1")
    namespace_provider.store("key2", "value2")
    namespace_provider.store("key3", "value3")
    
    # Retrieve and verify each one
    assert namespace_provider.get("key1") == "value1"
    assert namespace_provider.get("key2") == "value2"
    assert namespace_provider.get("key3") == "value3"
    
    # Check all keys are in the same namespace
    response = namespace_provider._client.get_secret_value(SecretId="test-namespace")
    secrets_dict = json.loads(response["SecretString"])
    assert len(secrets_dict) == 3
    assert secrets_dict["key1"] == "value1"
    assert secrets_dict["key2"] == "value2"
    assert secrets_dict["key3"] == "value3"
    
    # Delete one key and verify others remain
    namespace_provider.delete("key2")
    assert namespace_provider.get("key1") == "value1"
    assert namespace_provider.get("key2") is None
    assert namespace_provider.get("key3") == "value3"
    
    response = namespace_provider._client.get_secret_value(SecretId="test-namespace")
    secrets_dict = json.loads(response["SecretString"])
    assert len(secrets_dict) == 2
    assert "key2" not in secrets_dict


@pytest.mark.aws
def test_namespace_store_complex_values(namespace_provider):
    # Test storing and retrieving complex values in a namespace
    dict_value = {"nested": {"key": "value"}, "list": [1, 2, 3]}
    namespace_provider.store("complex_key", dict_value)
    
    fetched_value = namespace_provider.get("complex_key")
    assert fetched_value == dict_value
    
    # Check raw storage format
    response = namespace_provider._client.get_secret_value(SecretId="test-namespace")
    secrets_dict = json.loads(response["SecretString"])
    assert secrets_dict["complex_key"] == dict_value


@pytest.mark.aws
def test_namespace_nonexistent_key(namespace_provider):
    # Test getting a key that doesn't exist in the namespace
    assert namespace_provider.get("nonexistent_ns_key") is None


@pytest.mark.aws
def test_namespace_update_secret(namespace_provider):
    # Test updating a secret in the namespace
    namespace_provider.store("update_key", "original")
    assert namespace_provider.get("update_key") == "original"
    
    namespace_provider.store("update_key", "updated")
    assert namespace_provider.get("update_key") == "updated"
