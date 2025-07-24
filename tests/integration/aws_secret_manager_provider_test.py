import json
import os
import pytest
import boto3

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException, SecretNotFoundException


@pytest.fixture(scope="module")
def aws_client():
    """Creates a boto3 client for AWS Secrets Manager for test setup/teardown."""
    if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
        pytest.skip("AWS credentials not available in environment")
    
    try:
        client = boto3.client(service_name="secretsmanager", region_name="us-east-1")
        return client
    except Exception as e:
        pytest.skip(f"Error creating AWS client: {str(e)}")


@pytest.fixture(scope="module")
def provider(aws_client):
    """
    Creates real AWS secrets provider instance for integration testing.
    Tests will be skipped if AWS credentials aren't available.
    """
    provider = AWSSecretsProvider()
    
    # Test the connection works before continuing
    try:
        if not provider.connect():
            pytest.skip("Could not connect to AWS Secrets Manager")
    except Exception as e:
        pytest.skip(f"Error connecting to AWS: {str(e)}")
    
    yield provider


@pytest.fixture(scope="module")
def test_secret(aws_client):
    """Creates a test secret in AWS Secrets Manager for testing."""
    secret_id = "test_key"
    secret_value = "test_value"
    
    # Create the secret for testing
    try:
        aws_client.create_secret(
            Name=secret_id,
            SecretString=secret_value
        )
    except aws_client.exceptions.ResourceExistsException:
        # Update if it already exists
        aws_client.put_secret_value(
            SecretId=secret_id,
            SecretString=secret_value
        )
    
    yield secret_id, secret_value
    
    # Clean up
    try:
        aws_client.delete_secret(
            SecretId=secret_id,
            ForceDeleteWithoutRecovery=True
        )
    except:
        pass


@pytest.fixture(scope="module")
def test_complex_secret(aws_client):
    """Creates a test secret with complex JSON value."""
    secret_id = "complex_test_key"
    secret_value = {"key1": "value1", "key2": "value2"}
    
    # Create the secret for testing
    try:
        aws_client.create_secret(
            Name=secret_id,
            SecretString=json.dumps(secret_value)
        )
    except aws_client.exceptions.ResourceExistsException:
        # Update if it already exists
        aws_client.put_secret_value(
            SecretId=secret_id,
            SecretString=json.dumps(secret_value)
        )
    
    yield secret_id, secret_value
    
    # Clean up
    try:
        aws_client.delete_secret(
            SecretId=secret_id,
            ForceDeleteWithoutRecovery=True
        )
    except:
        pass


@pytest.fixture(scope="module")
def namespace_fixture(aws_client):
    """Creates a namespaced secret for testing."""
    namespace = "test-namespace"
    namespace_content = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
        "complex_key": {"nested": {"key": "value"}, "list": [1, 2, 3]}
    }
    
    # Create or update the namespace secret
    try:
        aws_client.create_secret(
            Name=namespace,
            SecretString=json.dumps(namespace_content)
        )
    except aws_client.exceptions.ResourceExistsException:
        aws_client.put_secret_value(
            SecretId=namespace,
            SecretString=json.dumps(namespace_content)
        )
    
    yield namespace, namespace_content
    
    # Clean up
    try:
        aws_client.delete_secret(
            SecretId=namespace,
            ForceDeleteWithoutRecovery=True
        )
    except:
        pass


@pytest.fixture(scope="module")
def namespace_provider(namespace_fixture):
    """Creates AWS secrets provider with namespace for integration testing."""
    namespace, _ = namespace_fixture
    
    if not (os.environ.get('AWS_ACCESS_KEY_ID') and os.environ.get('AWS_SECRET_ACCESS_KEY')):
        pytest.skip("AWS credentials not available in environment")
    
    provider = AWSSecretsProvider(namespace=namespace)
    
    # Test the connection works before continuing
    try:
        if not provider.connect():
            pytest.skip("Could not connect to AWS Secrets Manager")
    except Exception as e:
        pytest.skip(f"Error connecting to AWS: {str(e)}")
    
    yield provider


@pytest.mark.aws
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.aws
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.aws
def test_get_secret(provider, test_secret):
    secret_id, expected_value = test_secret
    fetched_value = provider.get(secret_id)
    assert fetched_value == expected_value


@pytest.mark.aws
def test_get_complex_secret(provider, test_complex_secret):
    secret_id, expected_value = test_complex_secret
    fetched_value = provider.get(secret_id)
    assert fetched_value == expected_value


@pytest.mark.aws
def test_get_nonexistent_secret(provider):
    with pytest.raises(SecretNotFoundException):
        provider.get("nonexistent_key_that_should_not_exist")


@pytest.mark.aws
def test_namespace_provider_ctor(namespace_provider, namespace_fixture):
    namespace, _ = namespace_fixture
    assert namespace_provider is not None
    assert namespace_provider._namespace == namespace


@pytest.mark.aws
def test_namespace_get_secret(namespace_provider, namespace_fixture):
    _, namespace_content = namespace_fixture
    
    # Test getting individual keys from namespace
    assert namespace_provider.get("key1") == namespace_content["key1"]
    assert namespace_provider.get("key2") == namespace_content["key2"]
    assert namespace_provider.get("key3") == namespace_content["key3"]
    
    # Test getting all secrets from namespace when key is None
    all_secrets = namespace_provider.get()
    assert all_secrets == namespace_content


@pytest.mark.aws
def test_namespace_get_complex_value(namespace_provider, namespace_fixture):
    _, namespace_content = namespace_fixture
    complex_value = namespace_provider.get("complex_key")
    assert complex_value == namespace_content["complex_key"]


@pytest.mark.aws
def test_namespace_get_nonexistent_key(namespace_provider):
    with pytest.raises(SecretNotFoundException):
        namespace_provider.get("nonexistent_ns_key_that_should_not_exist")