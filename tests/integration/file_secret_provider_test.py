import pytest

from secure_ai_toolset.secrets.file_secrets_provider import FileSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider, SecretProviderException


@pytest.fixture(scope="module")
def secret_provider() -> BaseSecretsProvider:
    """
    Fixture to provide a FileSecretsProvider instance.
    """
    return FileSecretsProvider()


def test_connect(secret_provider):
    """
    Test the connection to the secret provider.
    """
    assert secret_provider
    assert secret_provider.connect() is True


def test_get_nonexistent_secret(secret_provider):
    """
    Test getting a nonexistent secret returns None.
    """
    secret_key = 'secret1'
    secret_provider.delete(secret_key)
    secret = secret_provider.get(secret_key)
    assert secret is None


def test_create_get_nonexistent_secret(secret_provider):
    """
    Test creating, getting, and deleting a secret.
    """
    secret_key = 'key1'
    secret_provider.delete(secret_key)
    secret_value = 'value1'
    # Create secret, write and compare after get
    secret_provider.store(secret_key, secret_value)
    fetched_secret = secret_provider.get(secret_key)
    assert fetched_secret == secret_value

    # delete the secret and validate its empty
    secret_provider.delete(secret_key)
    fetched_secret = secret_provider.get(secret_key)
    assert not fetched_secret

    ## environment variables manager tests


@pytest.mark.parametrize("key", ["", None])
def test_delete_secret_none_empty(secret_provider, key):
    """
    Test deleting a secret with None or empty key raises an exception.
    """
    with pytest.raises(SecretProviderException):
        result = secret_provider.delete(key)
        assert result is None
