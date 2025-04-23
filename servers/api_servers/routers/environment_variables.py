"""
This module provides API endpoints for managing environment variables.

Endpoints:
    - GET /environment_variables/ : Retrieve all environment variables as a list of key-value pairs.
    - GET /environment_variables/{env_key}/ : Retrieve a specific environment variable by its key.
    - POST /environment_variables/{env_key}/ : Create or update an environment variable with a given key and value.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from servers.common import get_secret_provider

environment_variables_router = APIRouter()


class EnvironmentVariable(BaseModel):
    """
    Represents an environment variable with a key-value pair.

    Attributes:
        secret_key (str): The unique identifier for the environment variable.
        secret_value (SecretStr): The value associated with the environment variable key.
    """
    key: str
    value: str


class EnvironmentVariableInput(BaseModel):
    """
    Represents the input for creating or updating an environment variable.

    Attributes:
        value (SecretStr): The value of the environment variable.
    """
    value: str


@environment_variables_router.get("/environment_variables/",
                                  tags=["environment_variables"],
                                  response_model=list[EnvironmentVariable])
async def read_environment_variables():
    """
    Retrieve all environment variables as a list of key-value pairs.

    Returns:
        list[EnvironmentVariable]: A list of environment variables, where each contains a key and its associated value.
    """
    secret_provider = get_secret_provider()
    env_manager = EnvironmentVariablesManager(secret_provider)

    env_vars_dict = env_manager.list_env_vars()
    if env_vars_dict is None:
        raise HTTPException(status_code=404,
                            detail="No environment variables found")

    env_vars_array = [
        EnvironmentVariable(key=key, value=value)
        for key, value in env_vars_dict.items()
    ]
    return env_vars_array


@environment_variables_router.get("/environment_variables/{env_key}",
                                  tags=["environment_variables"],
                                  response_model=EnvironmentVariable)
async def get_environment_variable_by_key(env_key: str):
    """
    Retrieve a specific environment variable by its key.

    Args:
        env_key (str): The key of the environment variable to retrieve.

    Returns:
        EnvironmentVariable: The environment variable object containing the key and its associated value.

    Raises:
        HTTPException: If the environment variable is not found.
    """
    secret_provider = get_secret_provider()
    env_manager = EnvironmentVariablesManager(secret_provider)
    value = env_manager.get_env_var(key=env_key)
    return EnvironmentVariable(key=env_key, value=value)


@environment_variables_router.post("/environment_variables/{env_key}",
                                   tags=["environment_variables"],
                                   response_model=EnvironmentVariable)
async def create_environment_variable(env_key: str,
                                      env_var: EnvironmentVariableInput):
    """
    Create or update an environment variable with a given key and value.

    Args:
        env_key (str): The key of the environment variable to create or update.
        env_var (EnvironmentVariableInput): The environment variable object containing the value.

    Returns:
        EnvironmentVariable: The created or updated environment variable object.

    Raises:
        HTTPException: If an error occurs while setting the environment variable.
    """
    try:
        secret_provider = get_secret_provider()
        env_manager = EnvironmentVariablesManager(secret_provider)

        # Use EnvironmentVariablesManager to set the environment variable
        env_manager.add_env_var(key=env_key, value=env_var.value)

        return EnvironmentVariable(key=env_key, value=env_var.value)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
