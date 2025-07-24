# TODO: Move to credentials/base/secrets_provider.py
# this is a abstract class for secrets provider
import abc
import json
import logging
from typing import Optional, Type, Dict, Union, Any

from agent_guard_core.utils.flavor_manager import FlavorManager

logger = logging.getLogger(__name__)

class SecretProviderException(Exception):

    def __init__(self, message: str):
        super().__init__(message)

class SecretNotFoundException(SecretProviderException):
    def __init__(self, key: str):
        message = f"Secret with key '{key}' not found."
        super().__init__(message)
        self.key = key
        
class BaseSecretsProvider(abc.ABC):
    
    def __init__(self, namespace: Optional[str] = None, **kwargs) -> None:
        self._namespace = namespace

    def _get_raw_secret(self, key: Optional[str] = None) -> Optional[Union[str, Dict[str, Any]]]:
        """
        Retrieves the raw secret value from the provider by key.
        If key is None, retrieves all secrets.
        
        :param key: The name of the secret to retrieve, or None to get all secrets.
        :return: The raw secret string, a dictionary of all secrets, or None if not found.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        try:
            return self._get(key)
        except Exception as e:
            message = f"Error retrieving {'all secrets' if key is None else f'secret: {key}'}: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)
    
    def _try_parse(self, raw_secret: str) -> Union[str, Dict[str, str]]:
        """
        Parses the raw secret string into a dictionary or returns it as is if it's already a dictionary.
        :param raw_secret: The raw secret string to parse.
        :return: A dictionary representation of the secret or the raw string if it's not JSON.
        :raises SecretProviderException: If raw_secret is None or if parsing fails.
        """
        if raw_secret is None:
            logger.error("Raw secret is None")
            raise SecretProviderException("Raw secret is None")
        if isinstance(raw_secret, str):
            try:
                return json.loads(raw_secret)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                raise SecretProviderException(f"Failed to parse JSON: {str(e)}")
        elif isinstance(raw_secret, dict):
            return raw_secret
        else:
            logger.error(f"Unexpected type for raw secret: {type(raw_secret)}")
            raise SecretProviderException(f"Unexpected type for raw secret: {type(raw_secret)}")

    def get(self, key: Optional[str] = None) -> Union[str, Dict[str, str]]:
        """
        Retrieves a secret or all secrets from the provider.
        
        If key is None and namespace is None, returns all secrets.
        If key is None and namespace is provided, returns all secrets in the namespace.
        If key is provided and namespace is None, gets the specific secret.
        If key is provided and namespace is provided, gets the specific secret from the namespace.
        
        :param key: The name of the secret to retrieve, or None to get all secrets.
        :return: The secret value if key is provided, or a dictionary of all secrets if key is None.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        # Determine which secret ID to use
        secret_id = self._namespace or key
        
        # Get the raw secret string
        secret_text = self._get_raw_secret(key=secret_id)
        
        if secret_text is None:
            raise SecretNotFoundException(f"{secret_id}:{key}" if (key and secret_id!=key) else secret_id)
            
        if self._namespace is None:
            return secret_text
        
        secrets_dict = self._try_parse(secret_text)
        if isinstance(secrets_dict, dict):
            if self._namespace and key is None:
                # If no key is provided, return all secrets in the namespace
                return secrets_dict
            # If a key is provided, return the specific secret
            secret_value = secrets_dict.get(key)
            if secret_value is not None:
                return secret_value
            else:
                message = f"get: Key '{key}' not found in namespace {self._namespace}"
                logger.warning(message)
                raise SecretNotFoundException(key)
        else:
            message = f"get: Expected JSON object in namespace {self._namespace}, got: {type(secrets_dict)}"
            logger.warning(message)
            raise SecretProviderException(message)
        
    
    @abc.abstractmethod
    def connect(self) -> bool:
        ...

    @abc.abstractmethod
    def _get(self, key: Optional[str] = None) -> Optional[Union[str, Dict[str, str]]]:
        ...

secrets_provider_fm: FlavorManager[str, Type[BaseSecretsProvider]] = FlavorManager()