import os
import json
import logging
from typing import Any, Optional, Dict, Union

from dotenv import dotenv_values

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import (BaseSecretsProvider, SecretProviderException,
                                                           SecretNotFoundException, secrets_provider_fm)

logger = logging.getLogger(__name__)


@secrets_provider_fm.flavor(CredentialsProvider.FILE_DOTENV)
class FileSecretsProvider(BaseSecretsProvider):
    """
    FileSecretsProvider is a class that implements the BaseSecretsProvider interface.
    It provides methods to store, retrieve, and delete secrets in a file-based storage.
    """

    def __init__(self, namespace: str = ".env", **kwargs: Any) -> None:
        """
        Initialize the FileSecretsProvider with a namespace.

        :param namespace: The file path where secrets will be stored.
         It can include slashes to represent a directory structure.
        """
        if namespace is None:
            raise SecretProviderException("Namespace cannot be empty")

        # Use namespace as directory structure, last part as file name
        base_path, file_name = os.path.split(namespace)
        if not file_name:
            raise SecretProviderException("Namespace must include a file name")

        if base_path and not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        namespace = os.path.abspath(
            os.path.join(base_path, file_name))

        # Check if the file exists, if not, create it
        if not os.path.exists(namespace):
            try:
                with open(namespace, "w"):
                    pass  # Create an empty file
            except Exception as e:
                raise SecretProviderException(
                    f"Failed to create secrets file: {e}")
        
        super().__init__(namespace=namespace, **kwargs)

    def connect(self) -> bool:
        """
        Simulate a connection to the secrets storage.

        :return: True indicating the connection status.
        """
        return True

    def _parse_collection(self) -> Dict[str, str]:
        """
        Helper method to parse the dotenv file and return its contents as a dictionary.
        
        :return: Dictionary containing the key-value pairs from the dotenv file
        :raises SecretProviderException: If there is an error reading or parsing the file
        """
        try:
            collection = {}
            if not os.path.exists(self._namespace):
                return collection
                
            collection = dotenv_values(self._namespace)
                
            return dict(collection)
            
        except Exception as e:
            message = f"Error parsing secrets file: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)

    def _get(self, key: Optional[str] = None) -> Union[Optional[str], Dict[str, str]]:
        """
        Retrieve the entire collection of secrets from the file.
        For FileSecretsProvider, we always return the entire collection and let the caller
        filter for specific keys.

        :param key: Not used in this implementation. Included for compatibility with the interface.
        :return: A dictionary of all key-value pairs from the file.
        :raises SecretProviderException: If there is an error retrieving the secrets.
        """
        try:
            # Always return the entire collection, regardless of key
            return self._parse_collection()
        except Exception as e:
            message = f"Error retrieving secrets from file {self._namespace}: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)
        