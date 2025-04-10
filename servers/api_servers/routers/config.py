from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from servers.admin_ui.common import get_secret_provider

config_router = APIRouter()


class ServerConfig(BaseModel):
    """
    Represents the server configuration.

    Attributes:
        secret_provider (str): The current secret provider in use.
    """
    secret_provider: str


@config_router.get("/config/", tags=["config"], response_model=ServerConfig)
async def get_server_config():
    """
    Retrieve the server configuration, including the current secret provider.

    Returns:
        ServerConfig: An object containing the server configuration details.
    """
    try:
        secret_provider = get_secret_provider()

        secret_provider_name = str(
            type(secret_provider)).split("'")[1].split(".")[-1]

        config = ServerConfig(secret_provider=secret_provider_name)

        return config
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve server config: {str(e)}")
