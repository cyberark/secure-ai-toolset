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


def test_store(provider):
    try:
        provider.store("key", "secret")
        provider.store.assert_called_once_with("key", "secret")
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


def test_delete(provider):
    provider.delete.return_value = "deleted"
    try:
        result = provider.delete("key")
        assert result == "deleted"
        provider.delete.assert_called_once_with("key")
    except Exception:
        pytest.fail("Unexpected Exception raised")


def test_connect_failure(provider):
    provider.connect.side_effect = Exception("Connection failed")
    with pytest.raises(Exception) as excinfo:
        provider.connect()
    assert str(excinfo.value) == "Connection failed"
    provider.connect.assert_called_once()


def test_store_failure(provider):
    provider.store.side_effect = Exception("Store failed")
    with pytest.raises(Exception) as excinfo:
        provider.store("key", "secret")
    assert str(excinfo.value) == "Store failed"
    provider.store.assert_called_once_with("key", "secret")


def test_get_failure(provider):
    provider.get.side_effect = Exception("Get failed")
    with pytest.raises(Exception) as excinfo:
        provider.get("key")
    assert str(excinfo.value) == "Get failed"
    provider.get.assert_called_once_with("key")


def test_delete_failure(provider):
    provider.delete.side_effect = Exception("Delete failed")
    with pytest.raises(Exception) as excinfo:
        provider.delete("key")
    assert str(excinfo.value) == "Delete failed"
    provider.delete.assert_called_once_with("key")


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
    
    # Should return None for invalid JSON
    result = mock_conjur_provider.get("test-key")
    assert result is None


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.post')
@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_store_new(mock_get, mock_post, mock_conjur_provider):
    """Test storing a new secret in a namespace."""
    # Set up the response for the namespace request (namespace doesn't exist)
    get_response = MagicMock()
    get_response.status_code = 404
    mock_get.return_value = get_response
    
    # Set up the response for the post request
    post_response = MagicMock()
    post_response.status_code = 201
    mock_post.return_value = post_response
    
    # Store a secret in the namespace
    mock_conjur_provider.store("test-key", "test-value")
    
    # Verify get was called with namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]
    
    # Verify post was called with namespace and correct JSON
    assert mock_post.call_count > 0
    
    # Check at least one POST call has the right data
    found_correct_data = False
    for call in mock_post.call_args_list:
        args, kwargs = call
        if "test-namespace" in args[0] and "data" in kwargs:
            try:
                data = kwargs["data"]
                if isinstance(data, str):
                    data_dict = json.loads(data)
                    if data_dict.get("test-key") == "test-value":
                        found_correct_data = True
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
    
    assert found_correct_data, "No POST call contained the expected data"


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.post')
@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_store_update(mock_get, mock_post, mock_conjur_provider):
    """Test updating an existing secret in a namespace."""
    # Set up the response for the namespace request (namespace exists)
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.text = json.dumps({
        "test-key": "old-value",
        "other-key": "other-value"
    })
    mock_get.return_value = get_response
    
    # Set up the response for the post request
    post_response = MagicMock()
    post_response.status_code = 201
    mock_post.return_value = post_response
    
    # Update a secret in the namespace
    mock_conjur_provider.store("test-key", "new-value")
    
    # Verify get was called with namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]
    
    # Check at least one POST call has the right data
    found_correct_data = False
    for call in mock_post.call_args_list:
        args, kwargs = call
        if "test-namespace" in args[0] and "data" in kwargs:
            try:
                data = kwargs["data"]
                if isinstance(data, str):
                    data_dict = json.loads(data)
                    if (data_dict.get("test-key") == "new-value" and 
                        data_dict.get("other-key") == "other-value"):
                        found_correct_data = True
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
    
    assert found_correct_data, "No POST call contained the expected data with updated value"


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.post')
@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_delete_existing_key(mock_get, mock_post, mock_conjur_provider):
    """Test deleting an existing key from a namespace."""
    # Set up the response for the namespace request
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.text = json.dumps({
        "test-key": "test-value",
        "other-key": "other-value"
    })
    mock_get.return_value = get_response
    
    # Set up the response for the post request
    post_response = MagicMock()
    post_response.status_code = 201
    mock_post.return_value = post_response
    
    # Delete the key from the namespace
    mock_conjur_provider.delete("test-key")
    
    # Verify get was called with namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]
    
    # Check at least one POST call has the right data (without deleted key)
    found_correct_data = False
    for call in mock_post.call_args_list:
        args, kwargs = call
        if "test-namespace" in args[0] and "data" in kwargs:
            try:
                data = kwargs["data"]
                if isinstance(data, str):
                    data_dict = json.loads(data)
                    if "test-key" not in data_dict and data_dict.get("other-key") == "other-value":
                        found_correct_data = True
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
    
    assert found_correct_data, "No POST call contained the expected data without deleted key"


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.post')
@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_delete_nonexistent_key(mock_get, mock_post, mock_conjur_provider):
    """Test deleting a nonexistent key from a namespace."""
    # Set up the response for the namespace request
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.text = json.dumps({
        "other-key": "other-value"
    })
    mock_get.return_value = get_response
    
    # Delete a key that doesn't exist in the namespace
    mock_conjur_provider.delete("test-key")
    
    # Verify get was called with namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]
    
    # The POST should not be called with a data payload that updates the namespace,
    # since nothing needs to be changed
    namespace_unchanged = True
    for call in mock_post.call_args_list:
        args, kwargs = call
        if "test-namespace" in args[0] and "data" in kwargs:
            try:
                data = kwargs["data"]
                if isinstance(data, str):
                    data_dict = json.loads(data)
                    if data_dict != {"other-key": "other-value"}:
                        namespace_unchanged = False
            except (json.JSONDecodeError, AttributeError):
                continue
    
    assert namespace_unchanged, "Namespace was changed when deleting nonexistent key"


@patch('agent_guard_core.credentials.conjur_secrets_provider.requests.get')
def test_namespace_delete_nonexistent_namespace(mock_get, mock_conjur_provider):
    """Test deleting a key when the namespace doesn't exist."""
    # Set up the response for the namespace request
    get_response = MagicMock()
    get_response.status_code = 404
    mock_get.return_value = get_response
    
    # Delete should not raise an exception when namespace doesn't exist
    mock_conjur_provider.delete("test-key")
    
    # Verify get was called with namespace
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert "test-namespace" in args[0]
