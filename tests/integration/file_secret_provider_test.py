import os
import json
import tempfile
import shutil
import uuid
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


@pytest.fixture
def prepare_file_content():
    """Helper fixture to prepare content directly in a file"""
    def _prepare(file_path, contents):
        with open(file_path, "w") as f:
            for key, value in contents.items():
                f.write(f"{key}={value}\n")
    return _prepare


@pytest.fixture  # Changed to function scope (default)
def direct_provider(temp_dir) -> BaseSecretsProvider:
    """Provider without namespace for direct access testing"""
    # Create a unique file for each test
    file_path = os.path.join(temp_dir, f"direct_secrets_{uuid.uuid4()}")
    
    # Initialize with empty file
    with open(file_path, "w") as f:
        pass
        
    return FileSecretsProvider(namespace=file_path)


@pytest.fixture  # Changed to function scope (default)
def namespace_provider(temp_dir) -> BaseSecretsProvider:
    """Provider with namespace for testing namespace functionality"""
    namespace_path = os.path.join(temp_dir, f"namespace_secrets_{uuid.uuid4()}")
    
    # Initialize with empty JSON object
    with open(namespace_path, "w") as f:
        f.write("NAMESPACE={}\n")
        
    return FileSecretsProvider(namespace=namespace_path)


@pytest.fixture
def populated_provider(temp_dir) -> FileSecretsProvider:
    """Provider pre-populated with multiple secrets for testing get_all functionality"""
    provider_path = os.path.join(temp_dir, f"populated_secrets_{uuid.uuid4()}")
    
    # Create the provider
    provider = FileSecretsProvider(namespace=provider_path)
    
    # Populate with multiple secrets by writing directly to the file
    with open(provider_path, "w") as f:
        f.write("key1=value1\n")
        f.write("key2=value2\n")
        f.write("key3=value3\n")
    
    return provider


@pytest.fixture  # Changed to function scope (default)
def secret_provider_with_directory(temp_dir) -> BaseSecretsProvider:
    """Provider in a subdirectory"""
    # Create data directory if it doesn't exist
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, f"test_secrets_{uuid.uuid4()}")
    return FileSecretsProvider(namespace=file_path)


@pytest.fixture  # Changed to function scope (default)
def secret_provider_with_multiple_directories(temp_dir) -> BaseSecretsProvider:
    """Provider in a deeply nested subdirectory"""
    # Create nested directory structure
    nested_dir = os.path.join(temp_dir, "data", "multiple", "directories")
    os.makedirs(nested_dir, exist_ok=True)
    
    file_path = os.path.join(nested_dir, f"test_secrets_{uuid.uuid4()}")
    return FileSecretsProvider(namespace=file_path)


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


# Tests for getting all secrets with no key
def test_get_all_secrets_direct_access(direct_provider):
    """Test getting all secrets using get with no key parameter"""
    # First, set up some secrets
    direct_provider.store('key1', 'value1')
    direct_provider.store('key2', 'value2')
    direct_provider.store('key3', 'value3')
    
    # Get all secrets
    all_secrets = direct_provider.get()
    
    # Verify we got a dictionary with all our secrets
    assert isinstance(all_secrets, dict)
    assert len(all_secrets) >= 3  # Could be more if other tests added keys
    assert all_secrets['key1'] == 'value1'
    assert all_secrets['key2'] == 'value2'
    assert all_secrets['key3'] == 'value3'


def test_get_all_secrets_with_parse_collection(populated_provider):
    """Test that get() with no key returns the complete collection"""
    # Get all secrets
    all_secrets = populated_provider.get()
    
    # Access internal _parse_collection only for verification
    # Note: In real code, we wouldn't access this private method
    collection_for_verification = populated_provider._parse_collection()
    
    # Verify the content matches what we expect
    assert len(all_secrets) >= 3  # Could be more if other tests added keys
    assert all_secrets['key1'] == 'value1'
    assert all_secrets['key2'] == 'value2'
    assert all_secrets['key3'] == 'value3'
    
    # For test validation purposes only, verify get() returns same as parse_collection
    for key, value in collection_for_verification.items():
        assert all_secrets[key] == value


def test_empty_collection(temp_dir):
    """Test getting all secrets from an empty collection"""
    # Create a new provider with a fresh file
    empty_provider = FileSecretsProvider(namespace=os.path.join(temp_dir, "empty_secrets"))
    
    # Get all secrets
    all_secrets = empty_provider.get()
    
    # Should be an empty dictionary
    assert isinstance(all_secrets, dict)
    assert len(all_secrets) == 0


def test_get_after_delete_all(temp_dir, prepare_file_content):
    """Test getting all secrets after deleting all entries"""
    file_path = os.path.join(temp_dir, "delete_all_test")
    
    # Prepare the file with content
    with open(file_path, "w") as f:
        f.write("key1=value1\n")
        f.write("key2=value2\n")
        f.write("key3=value3\n")
    
    provider = FileSecretsProvider(namespace=file_path)
    
    # Get the initial collection
    initial_collection = provider.get()
    
    # Delete all keys
    for key in list(initial_collection.keys()):
        provider.delete(key)
    
    # Get the collection again
    empty_collection = provider.get()
    
    # Should be empty
    assert isinstance(empty_collection, dict)
    assert len(empty_collection) == 0


def test_mixed_content_file(temp_dir):
    """Test handling a file with both direct key-value pairs and a JSON entry"""
    file_path = os.path.join(temp_dir, "mixed_content.env")
    
    # Create a file with multiple entries
    with open(file_path, "w") as f:
        f.write("regular_key1=regular_value1\n")
        f.write("regular_key2=regular_value2\n")
        # No JSON entry in this case
    
    # Create provider
    provider = FileSecretsProvider(namespace=file_path)
    
    # Get all secrets
    all_secrets = provider.get()
    
    # Verify it returns all keys
    assert isinstance(all_secrets, dict)
    assert len(all_secrets) == 2
    assert all_secrets["regular_key1"] == "regular_value1"
    assert all_secrets["regular_key2"] == "regular_value2"


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


def test_env_file_format_handling(temp_dir):
    """Test handling a typical .env file with various environment variable formats"""
    file_path = os.path.join(temp_dir, "typical.env")
    
    # Create a file with typical .env file content
    with open(file_path, "w") as f:
        f.write("""# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=admin
DB_PASSWORD=s3cr3t!

# API configuration
API_URL=https://api.example.com/v1
API_KEY=abcdef123456
API_TIMEOUT=30

# Feature flags
FEATURE_DEBUG=true
FEATURE_EXPERIMENTAL=false

# Values with spaces and special characters
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)
WELCOME_MESSAGE=Hello, world! Welcome to our application.

# Empty value
EMPTY_VALUE=

# Quoted values
QUOTED_STRING="This is a quoted string with spaces"
SINGLE_QUOTED='Single quoted string'

# Comments and spacing should be ignored

# Environment selection
ENV=development
""")
    
    # Create provider
    provider = FileSecretsProvider(namespace=file_path)
    
    # Get all environment variables
    env_vars = provider.get()
    
    # Verify basic parsing works
    assert isinstance(env_vars, dict)
    assert len(env_vars) == 16  # All keys except comments
    
    # Test database config
    assert env_vars["DB_HOST"] == "localhost"
    assert env_vars["DB_PORT"] == "5432"
    assert env_vars["DB_NAME"] == "myapp"
    assert env_vars["DB_USER"] == "admin"
    assert env_vars["DB_PASSWORD"] == "s3cr3t!"
    
    # Test API config
    assert env_vars["API_URL"] == "https://api.example.com/v1"
    assert env_vars["API_KEY"] == "abcdef123456"
    assert env_vars["API_TIMEOUT"] == "30"
    
    # Test feature flags
    assert env_vars["FEATURE_DEBUG"] == "true"
    assert env_vars["FEATURE_EXPERIMENTAL"] == "false"
    
    # Test complex values
    assert env_vars["USER_AGENT"] == "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    assert env_vars["WELCOME_MESSAGE"] == "Hello, world! Welcome to our application."
    
    # Test empty value
    assert env_vars["EMPTY_VALUE"] == ""
    
    # Test quoted values (quotes typically preserved by dotenv)
    assert env_vars["QUOTED_STRING"] == "This is a quoted string with spaces"
    assert env_vars["SINGLE_QUOTED"] == "Single quoted string"
    
    # Test environment
    assert env_vars["ENV"] == "development"
    
    # Test storing and retrieving a new variable
    provider.store("NEW_VARIABLE", "new_value")
    assert provider.get("NEW_VARIABLE") == "new_value"
    
    # Get all variables again to check persistence
    updated_vars = provider.get()
    assert updated_vars["NEW_VARIABLE"] == "new_value"
    assert len(updated_vars) == 17  # Original 15 + 1 new
