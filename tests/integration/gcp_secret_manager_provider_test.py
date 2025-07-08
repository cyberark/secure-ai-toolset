import os
import pytest
from google.cloud import secretmanager

from agent_guard_core.credentials.gcp_secrets_manager_provider import GCPSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException


@pytest.fixture(scope="module")
def gcp_client():
    """
    Creates a GCP Secret Manager client for test setup/teardown.
    Tests will be skipped if GCP credentials aren't available.
    """
    # Check for GCP credentials
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        pytest.skip("GCP credentials not available in environment (GOOGLE_APPLICATION_CREDENTIALS), skipping GCP tests")
    
    # Get project ID from environment or use default
    project_id = os.environ.get('GCP_PROJECT_ID')
    if not project_id:
        pytest.skip("GCP_PROJECT_ID not set in environment, skipping GCP tests")
    
    # Create client for direct secret creation/cleanup
    try:
        client = secretmanager.SecretManagerServiceClient()
        return client, project_id
    except Exception as e:
        pytest.skip(f"Error creating GCP Secret Manager client: {str(e)}")


@pytest.fixture(scope="module")
def provider(gcp_client):
    """
    Creates GCP secrets provider instance for integration testing.
    """
    client, project_id = gcp_client
    
    provider = GCPSecretsProvider(project_id=project_id)
    
    # Test the connection works before continuing
    try:
        if not provider.connect():
            pytest.skip("Could not connect to GCP Secret Manager")
    except Exception as e:
        pytest.skip(f"Error connecting to GCP Secret Manager: {str(e)}")
    
    yield provider


@pytest.fixture
def setup_secret(gcp_client):
    """
    Fixture to create test secrets in GCP Secret Manager directly.
    Returns a function that can be called to create a secret.
    """
    client, project_id = gcp_client
    created_secrets = []
    
    def _create_secret(secret_id, secret_value):
        # Create the parent secret
        parent = f"projects/{project_id}"
        
        try:
            # First create the secret
            secret = client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
            
            # Then add the secret version with the value
            secret_value_bytes = secret_value.encode("UTF-8")
            version = client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": secret_value_bytes},
                }
            )
            
            created_secrets.append(secret_id)
            return secret.name
            
        except Exception as e:
            # Handle case where secret already exists
            if "already exists" in str(e):
                secret_name = f"{parent}/secrets/{secret_id}"
                # Add new version to existing secret
                secret_value_bytes = secret_value.encode("UTF-8")
                version = client.add_secret_version(
                    request={
                        "parent": secret_name,
                        "payload": {"data": secret_value_bytes},
                    }
                )
                created_secrets.append(secret_id)
                return secret_name
            raise
    
    yield _create_secret
    
    # Clean up all secrets created during the test
    for secret_id in created_secrets:
        try:
            name = f"projects/{project_id}/secrets/{secret_id}"
            client.delete_secret(request={"name": name})
        except Exception:
            pass  # Ignore errors during cleanup


@pytest.mark.gcp
def test_provider_ctor(provider):
    """Test provider constructor"""
    assert provider is not None


@pytest.mark.gcp
def test_provider_connect(provider):
    """Test provider connection"""
    assert provider.connect() is True


@pytest.mark.gcp
def test_get_secret(provider, setup_secret):
    """Test getting a secret"""
    # Setup a test secret
    secret_id = "test_get_secret"
    secret_value = "test_value"
    setup_secret(secret_id, secret_value)
    
    # Get and verify the secret
    fetched_value = provider.get(secret_id)
    assert fetched_value == secret_value


@pytest.mark.gcp
def test_get_nonexistent_secret(provider):
    """Test getting a nonexistent secret"""
    fetched_value = provider.get("nonexistent_key")
    assert fetched_value is None


@pytest.mark.gcp
def test_get_secret_dictionary(provider, setup_secret):
    """Test getting multiple secrets as a dictionary"""
    # Create test secrets
    test_secrets = {"key1": "value1", "key2": "value2", "key3": "value3"}
    
    # Setup each secret in GCP
    for key, value in test_secrets.items():
        setup_secret(key, value)
    
    # Get all secrets as dictionary
    fetched_secrets = provider.get()
    
    # Verify the test secrets are present in the returned dictionary
    for key, value in test_secrets.items():
        assert key in fetched_secrets
        assert fetched_secrets[key] == value


@pytest.mark.gcp
def test_get_with_none_key(provider):
    """Test getting a secret with None key"""
    # This should either return all secrets (get all) or raise an exception
    result = provider.get(None)
    # If None is treated as "get all secrets"
    if result is not None:
        assert isinstance(result, dict)
    # Otherwise, the behavior should be documented


@pytest.mark.gcp
def test_get_with_empty_key(provider):
    """Test getting a secret with empty key"""
    # Empty key should either return all secrets or None for not found
    result = provider.get("")
    # Empty key is typically treated as invalid, so expect None or empty result
    assert result is None or result == "" or isinstance(result, dict)