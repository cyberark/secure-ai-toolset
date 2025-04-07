"""
This module provides API endpoints for managing secrets.

Endpoints:
    - GET /secrets/ : Retrieve all secrets as a list of key-value pairs.
    - GET /secrets/{secret_key}/ : Retrieve a specific secret by its key.
    - POST /secrets/{secret_key}/ : Create or update a secret with a given key and value.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from servers.admin_ui.common import get_secret_provider

router = APIRouter()


class Secret(BaseModel):
    """
    Represents a secret with a key-value pair.

    Attributes:
        secret_key (str): The unique identifier for the secret.
        secret_value (str): The value associated with the secret key.
    """
    secret_key: str
    secret_value: str


@router.get("/secrets/", tags=["secrets"], response_model=list[Secret])
async def read_secrets():
    """
    Retrieve all secrets as a list of key-value pairs.

    Returns:
        list[Secret]: A list of secrets, where each secret contains a key and its associated value.
    """
    secret_provider = get_secret_provider()
    secrets_dictionary = secret_provider.get_secret_dictionary()
    secrets_list = [{
        "secret_key": key,
        "secret_value": value
    } for key, value in secrets_dictionary.items()]
    return secrets_list


@router.get("/secrets/{secret_key}/", tags=["secrets"], response_model=Secret)
async def get_secret_by_key(secret_key: str):
    """
    Retrieve a specific secret by its key.

    Args:
        secret_key (str): The key of the secret to retrieve.

    Returns:
        Secret: The secret object containing the key and its associated value.

    Raises:
        HTTPException: If the secret is not found or an error occurs.
    """
    secret_provider = get_secret_provider()
    try:
        secret_value = secret_provider.get(secret_key)
        if secret_value is None:
            raise HTTPException(status_code=404, detail="Secret not found")
        return {"secret_key": secret_key, "secret_value": secret_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/secrets/{secret_key}/", tags=["secrets"], response_model=Secret)
async def create_secret(secret_key: str, secret: Secret):
    """
    Create or update a secret with a given key and value.

    Args:
        secret_key (str): The key of the secret to create or update.
        secret (Secret): The secret object containing the key and value.

    Returns:
        Secret: The created or updated secret object.

    Raises:
        HTTPException: If an error occurs while storing the secret.
    """
    secret_provider = get_secret_provider()
    try:
        secret_provider.store(secret_key, secret.secret_value)
        return {"secret_key": secret_key, "secret_value": secret.secret_value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
