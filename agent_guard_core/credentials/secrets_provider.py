# TODO: Move to credentials/base/secrets_provider.py
# this is a abstract class for secrets provider
import abc
import json
import logging
from typing import Optional, Type

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

    def _get_raw_secret(self, key: str) -> Optional[str]:
        """
        Retrieves the raw secret value from the provider by key.
        
        :param key: The name of the secret to retrieve.
        :return: The raw secret string or None if not found.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        try:
            return self._get(key)
        except Exception as e:
            message = f"Error retrieving secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)
    
    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager.
        
        If namespace is provided, stores the secret as a key in the namespace collection.
        Otherwise, stores the secret directly with its key as the SecretId.
        
        :param key: The name of the secret key.
        :param secret: The secret value to store (string).
        :raises SecretProviderException: If key or secret is missing or if there is an error storing the secret.
        """

        if self._namespace is not None:
            
            collection_raw = self._get_raw_secret(key=self._namespace)

            try:
                collection = json.loads(collection_raw) if collection_raw else {}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from namespace {self._namespace}: {str(e)}")
                return None
            
            collection[key] = secret
            secret = json.dumps(collection)
            key = self._namespace
        
        self._store(key, secret)

    def get(self, key: Optional[str]) -> str:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        
        If namespace is provided, gets the secret as a key in the namespace collection.
        Otherwise, gets the secret directly by its key.
        
        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        # Determine which secret ID to use
        secret_id = self._namespace or key
        
        # Get the raw secret string
        secret_text = self._get_raw_secret(key=secret_id)
        
        if secret_text is None:
            raise SecretNotFoundException(key)
            
        if self._namespace is None:
            return secret_text
        
        try:
            secrets_dict = json.loads(secret_text)
            if isinstance(secrets_dict, dict):
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
        except json.JSONDecodeError as e:
            message = f"get: Failed to parse JSON from namespace {self._namespace}: {str(e)}"
            logger.error(message)
            return None
        
    
    @abc.abstractmethod
    def connect(self) -> bool:
        ...

    @abc.abstractmethod
    def _store(self, key: str, secret: str) -> None:
        ...

    @abc.abstractmethod
    def _get(self, key: str) -> Optional[str]:
        ...

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        ...

secrets_provider_fm: FlavorManager[str, Type[BaseSecretsProvider]] = FlavorManager()