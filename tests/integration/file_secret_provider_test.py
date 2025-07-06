import os
import json
import tempfile
import shutil
import pytest

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider, SecretProviderException, SecretNotFoundException


@pytest.fixture(scope="module")
def temp_dir():
    """Create a temporary directory for secret files during tests"""
    # Create a temporary directory
    test_dir = tempfile.mkdtemp()
    
    # Save the current working directory
    original_dir = os.getcwd()
    
    # Change to the temporary directory
    os.chdir(test_dir)
    
    yield test_dir
    
    # Clean up: Change back to original directory and remove temp directory
    os.chdir(original_dir)
    shutil.rmtree(test_dir)


@pytest.fixture(scope="module")
def direct_provider(temp_dir) -> BaseSecretsProvider:
    """Provider without namespace for direct access testing"""
    return FileSecretsProvider(namespace=os.path.join(temp_dir, "direct_secrets"))


@pytest.fixture(scope="module")
def namespace_provider(temp_dir) -> BaseSecretsProvider:
    """Provider with namespace for testing namespace functionality"""
    namespace_path = os.path.join(temp_dir, "namespace_secrets")
    provider = FileSecretsProvider(namespace=namespace_path)
    
    # Initialize the namespace with empty content
    with open(namespace_path, "w") as f:
        f.write("NAMESPACE={}\n")
        
    yield provider


@pytest.fixture(scope="module")
def secret_provider_with_directory(temp_dir) -> BaseSecretsProvider:
    """Provider in a subdirectory"""
    # Create data directory if it doesn't exist
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    return FileSecretsProvider(namespace=os.path.join(data_dir, "test_secrets"))


@pytest.fixture(scope="module")
def secret_provider_with_multiple_directories(temp_dir) -> BaseSecretsProvider:
    """Provider in a deeply nested subdirectory"""
    # Create nested directory structure
    nested_dir = os.path.join(temp_dir, "data", "multiple", "directories")
    os.makedirs(nested_dir, exist_ok=True)
    
    return FileSecretsProvider(namespace=os.path.join(nested_dir, "test_secrets"))


def test_connect(direct_provider):
    """Test basic connection functionality"""
    assert direct_provider
    assert direct_provider.connect() is True


# Direct access tests
def test_direct_store_get(direct_provider):
    """Test storing and getting a secret directly without namespace"""
    secret_key = 'direct_key'
    secret_value = 'direct_value'
    
    # Store the secret
    direct_provider.store(secret_key, secret_value)
    
    # Get and verify
    fetched_secret = direct_provider.get(secret_key)
    assert fetched_secret == secret_value


def test_direct_get_nonexistent(direct_provider):
    """Test getting a nonexistent secret directly without namespace"""
    # Try to get a nonexistent secret
    with pytest.raises(SecretNotFoundException) as excinfo:
        direct_provider.get('nonexistent_key')
    assert excinfo.value.key == 'nonexistent_key'


def test_direct_delete(direct_provider):
    """Test deleting a secret directly without namespace"""
    secret_key = 'to_delete'
    secret_value = 'delete_me'
    
    # Store a secret first
    direct_provider.store(secret_key, secret_value)
    
    # Verify it exists
    fetched_secret = direct_provider.get(secret_key)
    assert fetched_secret == secret_value
    
    # Delete it
    direct_provider.delete(secret_key)
    
    # Verify it's gone
    with pytest.raises(SecretNotFoundException) as excinfo:
        direct_provider.get(secret_key)
    assert excinfo.value.key == secret_key


def test_direct_delete_empty_key(direct_provider):
    """Test deleting with an empty key directly"""
    with pytest.raises(SecretProviderException) as excinfo:
        direct_provider.delete('')
    assert "key is missing" in str(excinfo.value)


# Namespace tests
def test_namespace_store_existing(namespace_provider):
    """Test storing in an existing namespace"""
    # First, set up some existing content
    namespace_provider.store('existing_key', 'existing_value')
    
    # Add a new key
    namespace_provider.store('new_key', 'new_value')
    
    # Verify both keys exist
    assert namespace_provider.get('existing_key') == 'existing_value'
    assert namespace_provider.get('new_key') == 'new_value'


def test_namespace_store_update(namespace_provider):
    """Test updating an existing key in a namespace"""
    # First, set a value
    namespace_provider.store('update_key', 'original_value')
    assert namespace_provider.get('update_key') == 'original_value'
    
    # Now update it
    namespace_provider.store('update_key', 'updated_value')
    assert namespace_provider.get('update_key') == 'updated_value'
    
    # Make sure other keys weren't affected
    assert namespace_provider.get('existing_key') == 'existing_value'


def test_namespace_get_existing(namespace_provider):
    """Test getting an existing key from a namespace"""
    # Set up a key
    namespace_provider.store('get_key', 'get_value')
    
    # Retrieve it
    result = namespace_provider.get('get_key')
    assert result == 'get_value'


def test_namespace_get_nonexistent_key(namespace_provider):
    """Test getting a nonexistent key from an existing namespace"""
    # Try to get a key that doesn't exist in the namespace
    with pytest.raises(SecretNotFoundException) as excinfo:
        namespace_provider.get('nonexistent_ns_key')
    assert excinfo.value.key == 'nonexistent_ns_key'


def test_namespace_delete(namespace_provider):
    """Test deleting a key from a namespace"""
    # Set up some keys
    namespace_provider.store('delete_key', 'delete_value')
    namespace_provider.store('keep_key', 'keep_value')
    
    # Verify they exist
    assert namespace_provider.get('delete_key') == 'delete_value'
    assert namespace_provider.get('keep_key') == 'keep_value'
    
    # Delete one key
    namespace_provider.delete('delete_key')
    
    # Verify it's gone but the other remains
    with pytest.raises(SecretNotFoundException):
        namespace_provider.get('delete_key')
    assert namespace_provider.get('keep_key') == 'keep_value'


def test_namespace_with_directory(secret_provider_with_directory):
    """Test namespace in a subdirectory"""
    secret_key = 'dir_key'
    secret_value = 'dir_value'
    
    # Create secret, write and compare after get
    secret_provider_with_directory.store(secret_key, secret_value)
    fetched_secret = secret_provider_with_directory.get(secret_key)
    assert fetched_secret == secret_value
    
    # Delete the secret and validate it's gone
    secret_provider_with_directory.delete(secret_key)
    with pytest.raises(SecretNotFoundException) as excinfo:
        secret_provider_with_directory.get(secret_key)
    assert excinfo.value.key == secret_key


def test_namespace_with_multiple_directories(secret_provider_with_multiple_directories):
    """Test namespace in a deeply nested directory structure"""
    secret_key = 'multi_dir_key'
    secret_value = 'multi_dir_value'
    
    # Create secret, write and compare after get
    secret_provider_with_multiple_directories.store(secret_key, secret_value)
    fetched_secret = secret_provider_with_multiple_directories.get(secret_key)
    assert fetched_secret == secret_value
    
    # Delete the secret and validate it's gone
    secret_provider_with_multiple_directories.delete(secret_key)
    with pytest.raises(SecretNotFoundException) as excinfo:
        secret_provider_with_multiple_directories.get(secret_key)
    assert excinfo.value.key == secret_key


def test_empty_namespace_error():
    """Test that empty namespace raises an exception"""
    with pytest.raises(SecretProviderException) as excinfo:
        FileSecretsProvider(namespace=None)
    assert "Namespace cannot be empty" in str(excinfo.value)


def test_complex_values(direct_provider):
    """Test storing and retrieving complex values"""
    # Try storing a dictionary
    dict_value = {"key1": "value1", "nested": {"inner": "value"}}
    direct_provider.store("complex_key", json.dumps(dict_value))
    
    # Retrieve and verify
    fetched_value = direct_provider.get("complex_key")
    assert json.loads(fetched_value) == dict_value


def test_namespace_understanding(temp_dir):
    """Test that clarifies how 'namespace' is used in FileSecretsProvider"""
    # Create two providers with different namespaces (files)
    provider1 = FileSecretsProvider(namespace=os.path.join(temp_dir, "file1.env"))
    provider2 = FileSecretsProvider(namespace=os.path.join(temp_dir, "file2.env"))
    
    # Store the same key in both providers
    provider1.store("same_key", "value1")
    provider2.store("same_key", "value2")
    
    # Keys are stored in separate files, so they don't conflict
    assert provider1.get("same_key") == "value1"
    assert provider2.get("same_key") == "value2"
    
    # Each file is independent - deleting from one doesn't affect the other
    provider1.delete("same_key")
    with pytest.raises(SecretNotFoundException):
        provider1.get("same_key")
    assert provider2.get("same_key") == "value2"
