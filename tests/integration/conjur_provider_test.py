import shutil
from pathlib import Path

import pytest

from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException, SecretNotFoundException


@pytest.fixture(scope="module")
def provider():
    """
    Creates real Conjur secrets provider instance for integration testing.
    Tests will be skipped if Conjur credentials aren't available.
    """
    # Backup the existing .env and copy .env.conjur to .env
    env_path = Path(".env")
    backup_path = Path(".env.backup")
    conjur_env_path = Path(".env.conjur")

    if not conjur_env_path.exists():
        pytest.skip(".env.conjur file not found, skipping Conjur tests")

    if env_path.exists():
        shutil.copy(env_path, backup_path)
    shutil.copy(conjur_env_path, env_path)

    provider_instance = ConjurSecretsProvider(namespace='data/test-toolset')
    
    # Test the connection works before continuing
    try:
        if not provider_instance.connect():
            pytest.skip("Could not connect to Conjur")
    except Exception as e:
        pytest.skip(f"Error connecting to Conjur: {str(e)}")

    yield provider_instance

    # Restore the backup after use
    if backup_path.exists():
        shutil.copy(backup_path, env_path)
        backup_path.unlink()
    else:
        env_path.unlink()


@pytest.mark.conjur
def test_provider_ctor(provider):
    assert provider is not None


@pytest.mark.conjur
def test_provider_connect(provider):
    assert provider.connect() is True


@pytest.mark.conjur
def test_get_existing_secret(provider):
    """
    Test getting an existing secret.
    Note: This test assumes a secret with key 'test_secret' exists in the Conjur vault.
    """
    try:
        fetched_value = provider.get("test_secret")
        assert fetched_value is not None
        assert isinstance(fetched_value, str)
    except SecretNotFoundException:
        pytest.skip("Test secret 'test_secret' not found in Conjur. Please add it manually for this test.")


@pytest.mark.conjur
def test_get_namespace_secret(provider):
    """
    Test getting a secret from the namespace.
    Note: This test assumes a secret exists in the namespace used by the provider.
    """
    try:
        # Get all secrets in the namespace
        secrets = provider.get()
        assert secrets is not None
        assert isinstance(secrets, dict)
        assert len(secrets) > 0
        
        # Get the first secret key and try to retrieve it directly
        first_key = next(iter(secrets))
        fetched_value = provider.get(first_key)
        assert fetched_value is not None
        assert fetched_value == secrets[first_key]
    except SecretNotFoundException:
        pytest.skip("No secrets found in the namespace. Please add some secrets manually for this test.")


@pytest.mark.conjur
def test_get_nonexistent_secret(provider):
    """Test getting a nonexistent secret raises the correct exception."""
    with pytest.raises(SecretNotFoundException):
        provider.get("nonexistent_key_" + str(uuid.uuid4()))


@pytest.mark.conjur
def test_get_with_empty_key(provider):
    """Test getting a secret with an empty key raises the correct exception."""
    with pytest.raises(SecretProviderException):
        provider.get("")


@pytest.mark.conjur
def test_get_with_none_key(provider):
    """
    Test getting all secrets when key is None.
    This should return all secrets in the namespace.
    """
    try:
        secrets = provider.get(None)
        assert secrets is not None
        assert isinstance(secrets, dict)
    except SecretProviderException as e:
        pytest.fail(f"get(None) should not raise an exception: {str(e)}")