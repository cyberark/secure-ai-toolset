import os
import uuid

import pytest

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.gcp_secrets_manager_provider import GCPSecretsProvider


@pytest.fixture(params=[
    AWSSecretsProvider(region_name="us-east-1", namespace=""),
    AWSSecretsProvider(region_name="us-east-1", namespace="test_asm_1"),
    GCPSecretsProvider(project_id="test-project-1"),
    FileSecretsProvider(namespace="ns_test1"),
])
def env_manager(request):
    """
    Fixture to create an instance of EnvironmentVariablesManager with AWSParameterStoreProvider or AWSSecretsProvider.
    This fixture is used to provide a clean instance for each test case.
    """
    secret_provider = request.param
    return EnvironmentVariablesManager(secret_provider=secret_provider)


def test_aws_secrets_manager_connect(env_manager):
    """
    Test case to verify the functionality of the AWS Secrets Manager provider.
    
    Steps:
    1. Verify that the env_manager instance is created.
    2. Fetch the value of a secret from the AWS Secrets Manager.
    3. Verify that the fetched value is not None.
    """
    assert env_manager
    assert env_manager.secret_provider
    result = env_manager.secret_provider.connect()
    assert result


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
    env_manager._add_env_var(key=key, value=value)

    fetched_value = env_manager._get_env_var(key)
    assert fetched_value == value

    env_manager._remove_env_var(key)
    fetched_value = env_manager._get_env_var(key)
    assert fetched_value is None


def test_list_env_vars_with_spaces(env_manager):
    assert env_manager
    env_vars_list = env_manager.list_env_vars()
    assert env_vars_list is not None

    key = f"key_{uuid.uuid4()}"
    value = f"value_{uuid.uuid4()}"
    dirty_key = f"  {key}   "
    dirty_value = f"  {value}  "

    # storing key and values wrapped with spaces
    env_manager._add_env_var(key=dirty_key, value=dirty_value)

    # check that the key and value where sanitized
    fetched_value = env_manager._get_env_var(key)
    assert fetched_value == value


def test_add_value_with_space_inside():

    file_content = """
    a1 = bbb
    a2= b b
    a3  = b b
    a4 = "b b"
    """

    file_name = '.env'
    # write the file content to a file called .env
    with open(file_name, 'w') as file:
        file.write(file_content)

    env_manager = EnvironmentVariablesManager(
        FileSecretsProvider())
    assert env_manager
    env_vars_list = env_manager.list_env_vars()
    assert env_vars_list is not None
    assert env_vars_list.get('a1') == 'bbb'
    assert env_vars_list.get('a2') == 'b b'
    assert env_vars_list.get('a3') == 'b b'
    assert env_vars_list.get('a4') == 'b b'

    # delete file
    if os.path.exists(file_name):
        os.remove(file_name)

    # check env vars are empty after deleting the file
    env_manager = EnvironmentVariablesManager(
        FileSecretsProvider())
    env_vars_list = env_manager.list_env_vars()
    assert env_vars_list == {}


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
    keys_values = {
        f"key_{uuid.uuid4()}": f"value_{uuid.uuid4()}"
        for _ in range(5)
    }
    # store new environment
    for key, value in keys_values.items():
        env_manager._add_env_var(key=key, value=value)

    # Populate environment variables
    env_manager.populate_env_vars()

    # Check they exist
    for key, value in keys_values.items():
        fetched_value = env_manager._get_env_var(key)
        os_env_value = os.environ.get(key)
        assert os_env_value == fetched_value

    # Depopulate environment variables
    env_manager.depopulate_env_vars()

    # Check they don't exist as environment variables
    for key in keys_values.keys():
        fetched_os_env_value = os.environ.get(key)
        assert fetched_os_env_value is None

    # remove new environment variables from repository
    for key, value in keys_values.items():
        env_manager._remove_env_var(key=key)
        fetched_removed_value = env_manager._get_env_var(key=key)
        assert not fetched_removed_value
