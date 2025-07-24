import functools
import logging
from typing import Any, Callable, TypeVar

import requests

from agent_guard_core.api.sia.models import ShortLivedPasswordRequest

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='RestApiProvider')

class RestApiProvider:
    _base_url: str
    
def api_endpoint(endpoint: str) -> Callable: # type: ignore
    def decorator(func: Callable) -> Callable: # type: ignore
        @functools.wraps(func)
        def wrapper(self: T, *args, **kwargs) -> Any: # type: ignore
            url = f"{self._base_url}{endpoint}"
            if "url" in kwargs:
                url = kwargs.pop("url")  # Use provided URL if available
            else:
                kwargs["url"] = url  # Add default URL to kwargs if not provided

            return func(self, *args, **kwargs)

        return wrapper

    return decorator

class SecureInfraAccessException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class SecureInfraAccessHandler:
    def __init__(self, tenant_id: str, access_token: str):
        self._tenant_id = tenant_id
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        })

        self._base_url = f"https://{tenant_id}.dpa.integration-cyberark.cloud/api"

    @api_endpoint("/adb/sso/acquire")
    def get_short_lived_password(self, url: str = None) -> str:
        request = ShortLivedPasswordRequest()
        
        response = self._session.post(url, json=request.model_dump())
        response.raise_for_status()
        
        token = response.json().get("token", {}).get("key")
        if token is None:
            raise SecureInfraAccessException("Failed to acquire short-lived password: 'token' key not found in response.")

        logger.debug(f"Short-lived password acquired. Token metadata: {response.json().get('metadata')}")
        return token