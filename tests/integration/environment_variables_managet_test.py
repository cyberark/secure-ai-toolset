import os
import uuid
import pytest
from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.environment_manager import EnvironmentVariablesManager

@pytest.fixture
def env_manager():
    """
    Fixture to create an instance of EnvironmentVariablesManager with AWSSecretsProvider.
    This fixture is used to provide a clean instance for each test case.
    """
    secret_provider = AWSSecretsProvider()
    return EnvironmentVariablesManager(secret_provider=secret_provider)

def test_list_env_vars_positive(env_manager):
    """
    Test case to verify the functionality of listing, adding, fetching, and removing environment variables.
    
    Steps:
    1. Verify that the env_manager instance is created.
    2. List the current environment variables and ensure the list is not None.
    3. Add a new environment variable with a unique key and value.
    4. Fetch the value of the newly added environment variable and verify it matches the expected value.
    5. Remove the environment variable.
    6. Attempt to fetch the removed environment variable and verify it returns None.
    """
    assert env_manager
    env_vars_list = env_manager.list_env_vars()
    assert env_vars_list is not None

    key = f"key_{uuid.uuid4()}"
    value = f"value_{uuid.uuid4()}"
    env_manager.add_env_var(key=key, value=value)

    fetched_value = env_manager.get_env_var(key)
    assert fetched_value == value

    env_manager.remove_env_var(key)
    fetched_value = env_manager.get_env_var(key)
    assert fetched_value is None

def test_populate_and_depopulate_env_vars(env_manager):
    """
    Test case to verify the functionality of populating and depopulating environment variables.
    
    Steps:
    1. Create a dictionary of unique key-value pairs.
    2. Add each key-value pair to the environment manager.
    3. Populate the environment variables from the environment manager.
    4. Verify that each environment variable is correctly set in the OS environment.
    5. Depopulate the environment variables from the OS environment.
    6. Verify that each environment variable is removed from the OS environment.
    7. Remove each key-value pair from the environment manager.
    8. Verify that each key-value pair is removed from the environment manager.
    """
    keys_values = {f"key_{uuid.uuid4()}": f"value_{uuid.uuid4()}" for _ in range(5)}
    # store new environment
    for key, value in keys_values.items():
        env_manager.add_env_var(key=key, value=value)

    # Populate environment variables
    env_manager.populate_env_vars()

    # Check they exist 
    for key, value in keys_values.items():
        fetched_value = env_manager.get_env_var(key)
        os_env_value = os.environ.get(key)
        assert os_env_value == fetched_value

    # Depopulate environment variables
    env_manager.depopulate_env_vars()

    # Check they don't exist as environment variables
    for key in keys_values.keys():
        fetched_os_env_value = os.environ.get(key)
        assert fetched_os_env_value is None

    # remove new environment
    for key, value in keys_values.items():
        env_manager.remove_env_var(key=key)
        fetched_removed_value = env_manager.get_env_var(key=key)
        assert not fetched_removed_value




