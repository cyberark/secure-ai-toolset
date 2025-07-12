import json
from unittest.mock import MagicMock, patch
import pytest

from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException, SecretNotFoundException


@pytest.fixture(params=[ConjurSecretsProvider])
def provider(request):
    return MagicMock(spec=request.param)


@pytest.fixture
def mock_response():
    """Creates a mock response object with configurable status code and text."""
    response = MagicMock()
    response.status_code = 200
    response.text = "test-value"
    return response


@pytest.fixture
def mock_conjur_provider():
    """Creates a mock ConjurSecretsProvider with controlled behavior."""
    with patch.multiple('agent_guard_core.credentials.conjur_secrets_provider', 
                        requests=MagicMock(),
                        load_dotenv=MagicMock(),
                        os=MagicMock()):
        # Mock environment variables
        mocked_os = patch('os.getenv')
        mock_getenv = mocked_os.start()
        mock_getenv.return_value = "mock-value"

        # Create provider instance
        provider = ConjurSecretsProvider(namespace="test-namespace")
        
        # Mock the connect method
        provider.connect = MagicMock(return_value=True)
        provider._get_conjur_headers = MagicMock(return_value={"Authorization": "mock-token", "Content-Type": "text/plain"})
        
        yield provider
        
        mocked_os.stop()


def test_connect(provider):
    provider.connect.return_value = True
    try:
        result = provider.connect()
        assert result == True
        provider.connect.assert_called_once()
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_get(provider):
    provider.get.return_value = "secret"
    try:
        result = provider.get("key")
        assert result == "secret"
        provider.get.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_connect_failure(provider):
    provider.connect.side_effect = Exception("Connection failed")
    with pytest.raises(Exception) as excinfo:
        provider.connect()
    assert str(excinfo.value) == "Connection failed"
    provider.connect.assert_called_once()


def test_get_failure(provider):
    provider.get.side_effect = Exception("Get failed")
    with pytest.raises(Exception) as excinfo:
        provider.get("key")
    assert str(excinfo.value) == "Get failed"
    provider.get.assert_called_once_with("key")


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_get_existing(mock_get, mock_conjur_provider):
    """Test getting an existing secret from a namespace."""
    # Set up the response for the namespace request
    namespace_response = MagicMock()
    namespace_response.status_code = 200
    namespace_response.text = json.dumps({
        "test-key": "test-value",
        "other-key": "other-value"
    })
    mock_get.return_value = namespace_response
    
    # Call the method
    result = mock_conjur_provider.get("test-key")
    
    # Verify the result is correct
    assert result == "test-value"
    
    # Verify the request was made with the namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_get_all(mock_get, mock_conjur_provider):
    """Test getting all secrets from a namespace."""
    # Set up the response for the namespace request
    namespace_data = {
        "test-key": "test-value",
        "other-key": "other-value"
    }
    namespace_response = MagicMock()
    namespace_response.status_code = 200
    namespace_response.text = json.dumps(namespace_data)
    mock_get.return_value = namespace_response
    
    # Call the method with no key to get all secrets
    result = mock_conjur_provider.get()
    
    # Verify the result is correct
    assert result == namespace_data
    
    # Verify the request was made with the namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_get_nonexistent_key(mock_get, mock_conjur_provider):
    """Test getting a nonexistent key from an existing namespace."""
    # Set up the response for the namespace request
    namespace_response = MagicMock()
    namespace_response.status_code = 200
    namespace_response.text = json.dumps({
        "other-key": "other-value"
    })
    mock_get.return_value = namespace_response
    
    # Expect exception when key doesn't exist in namespace
    with pytest.raises(SecretNotFoundException) as excinfo:
        mock_conjur_provider.get("test-key")
    
    # Verify the exception has the correct key
    assert excinfo.value.key == "test-key"


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_get_nonexistent_namespace(mock_get, mock_conjur_provider):
    """Test getting a key when the namespace doesn't exist."""
    # Set up the response for the namespace request
    namespace_response = MagicMock()
    namespace_response.status_code = 404
    mock_get.return_value = namespace_response
    
    # Expect exception when namespace doesn't exist
    with pytest.raises(SecretNotFoundException) as excinfo:
        mock_conjur_provider.get("test-key")
    
    # Verify the exception has the correct message
    assert "test-key" in str(excinfo.value)


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_get_invalid_json(mock_get, mock_conjur_provider):
    """Test getting from a namespace with invalid JSON content."""
    # Set up the response for the namespace request
    namespace_response = MagicMock()
    namespace_response.status_code = 200
    namespace_response.text = "not valid json"
    mock_get.return_value = namespace_response
    
    # Should raise SecretProviderException for invalid JSON
    with pytest.raises(SecretProviderException) as excinfo:
        mock_conjur_provider.get("test-key")
    
    # Verify the exception has the correct message
    assert "Failed to parse JSON" in str(excinfo.value)
    
    # Verify the request was made with the namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_direct_get(mock_get, mock_conjur_provider):
    """Test getting a secret directly (without a namespace)."""
    # Create a provider without namespace
    direct_provider = ConjurSecretsProvider()
    direct_provider._get_conjur_headers = MagicMock(
        return_value={"Authorization": "mock-token", "Content-Type": "text/plain"}
    )
    
    # Set up the response
    direct_response = MagicMock()
    direct_response.status_code = 200
    direct_response.text = "direct-value"
    mock_get.return_value = direct_response
    
    # Call the method
    result = direct_provider.get("direct-key")
    
    # Verify the result is correct
    assert result == "direct-value"
    
    # Verify the request was made directly to the key
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "direct-key" in args[0]


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_direct_get_not_found(mock_get, mock_conjur_provider):
    """Test getting a nonexistent secret directly."""
    # Create a provider without namespace
    direct_provider = ConjurSecretsProvider()
    direct_provider._get_conjur_headers = MagicMock(
        return_value={"Authorization": "mock-token", "Content-Type": "text/plain"}
    )
    
    # Set up the response for a nonexistent secret
    not_found_response = MagicMock()
    not_found_response.status_code = 404
    mock_get.return_value = not_found_response
    
    # Expect exception when secret doesn't exist
    with pytest.raises(SecretNotFoundException) as excinfo:
        direct_provider.get("nonexistent-key")
    
    # Verify the exception has the correct key
    assert excinfo.value.key == "nonexistent-key"