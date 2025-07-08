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
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            for key, value in contents.items():
                f.write(f"{key}={value}\n")
    return _prepare


@pytest.fixture
def direct_provider(temp_dir, prepare_file_content) -> BaseSecretsProvider:
    """Provider with prepopulated test data"""
    file_path = os.path.join(temp_dir, f"direct_secrets_{uuid.uuid4()}")
    
    # Create test data
    test_data = {
        "direct_key": "direct_value",
        "test_key": "test_value"
    }
    prepare_file_content(file_path, test_data)
        
    return FileSecretsProvider(namespace=file_path)


@pytest.fixture
def populated_provider(temp_dir, prepare_file_content) -> FileSecretsProvider:
    """Provider pre-populated with multiple secrets for testing get functionality"""
    provider_path = os.path.join(temp_dir, f"populated_secrets_{uuid.uuid4()}")
    
    # Prepare test data
    test_data = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3"
    }
    prepare_file_content(provider_path, test_data)
    
    return FileSecretsProvider(namespace=provider_path)


@pytest.fixture
def secret_provider_with_directory(temp_dir, prepare_file_content) -> BaseSecretsProvider:
    """Provider in a subdirectory with prepopulated data"""
    # Create data directory if it doesn't exist
    data_dir = os.path.join(temp_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, f"test_secrets_{uuid.uuid4()}")
    
    # Create test data
    test_data = {
        "dir_key": "dir_value"
    }
    prepare_file_content(file_path, test_data)
    
    return FileSecretsProvider(namespace=file_path)


@pytest.fixture
def secret_provider_with_multiple_directories(temp_dir, prepare_file_content) -> BaseSecretsProvider:
    """Provider in a deeply nested subdirectory with prepopulated data"""
    # Create nested directory structure
    nested_dir = os.path.join(temp_dir, "data", "multiple", "directories")
    os.makedirs(nested_dir, exist_ok=True)
    
    file_path = os.path.join(nested_dir, f"test_secrets_{uuid.uuid4()}")
    
    # Create test data
    test_data = {
        "multi_dir_key": "multi_dir_value"
    }
    prepare_file_content(file_path, test_data)
    
    return FileSecretsProvider(namespace=file_path)


def test_connect(direct_provider):
    """Test basic connection functionality"""
    assert direct_provider
    assert direct_provider.connect() is True


def test_direct_get(direct_provider):
    """Test getting a secret directly without namespace"""
    # Get and verify
    fetched_secret = direct_provider.get("direct_key")
    assert fetched_secret == "direct_value"


def test_direct_get_nonexistent(direct_provider):
    """Test getting a nonexistent secret directly without namespace"""
    # Try to get a nonexistent secret
    with pytest.raises(SecretNotFoundException) as excinfo:
        direct_provider.get('nonexistent_key')
    assert excinfo.value.key == 'nonexistent_key'


# Tests for getting all secrets with no key
def test_get_all_secrets_direct_access(direct_provider):
    """Test getting all secrets using get with no key parameter"""
    # Get all secrets
    all_secrets = direct_provider.get()
    
    # Verify we got a dictionary with all our secrets
    assert isinstance(all_secrets, dict)
    assert len(all_secrets) >= 2  # Could be more if other tests added keys
    assert all_secrets['direct_key'] == 'direct_value'
    assert all_secrets['test_key'] == 'test_value'


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
    empty_file = os.path.join(temp_dir, "empty_secrets")
    
    # Create an empty file
    with open(empty_file, "w") as f:
        pass
    
    empty_provider = FileSecretsProvider(namespace=empty_file)
    
    # Get all secrets
    all_secrets = empty_provider.get()
    
    # Should be an empty dictionary
    assert isinstance(all_secrets, dict)
    assert len(all_secrets) == 0


def test_mixed_content_file(temp_dir, prepare_file_content):
    """Test handling a file with both direct key-value pairs"""
    file_path = os.path.join(temp_dir, "mixed_content.env")
    
    # Create test data
    test_data = {
        "regular_key1": "regular_value1",
        "regular_key2": "regular_value2"
    }
    prepare_file_content(file_path, test_data)
    
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
    # Get and verify the pre-populated secret
    fetched_secret = secret_provider_with_directory.get("dir_key")
    assert fetched_secret == "dir_value"


def test_namespace_with_multiple_directories(secret_provider_with_multiple_directories):
    """Test namespace in a deeply nested directory structure"""
    # Get and verify the pre-populated secret
    fetched_secret = secret_provider_with_multiple_directories.get("multi_dir_key")
    assert fetched_secret == "multi_dir_value"


def test_empty_namespace_error():
    """Test that empty namespace raises an exception"""
    with pytest.raises(SecretProviderException) as excinfo:
        FileSecretsProvider(namespace=None)
    assert "Namespace cannot be empty" in str(excinfo.value)


def test_complex_values(temp_dir, prepare_file_content):
    """Test retrieving complex values"""
    # Create a file with a JSON string value
    file_path = os.path.join(temp_dir, "complex_values.env")
    dict_value = {"key1": "value1", "nested": {"inner": "value"}}
    
    test_data = {
        "complex_key": json.dumps(dict_value)
    }
    prepare_file_content(file_path, test_data)
    
    # Create provider and retrieve value
    provider = FileSecretsProvider(namespace=file_path)
    fetched_value = provider.get("complex_key")
    
    # Verify the value
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