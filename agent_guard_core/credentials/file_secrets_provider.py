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
            if not os.path.exists(self._namespace):
                return {}
                
            collection = dotenv_values(self._namespace)
            if collection is None:
                collection = {}
                
            # Check if this is actually a JSON string stored in the file
            if len(collection) == 1 and list(collection.keys())[0] == self._namespace:
                # This means the file contains a single entry with the file path as key
                try:
                    json_str = collection[self._namespace]
                    parsed_json = json.loads(json_str)
                    if isinstance(parsed_json, dict):
                        return parsed_json
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # Otherwise, return the collection as is
            return dict(collection)
            
        except Exception as e:
            message = f"Error parsing secrets file: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)

    def _store(self, key: str, secret: str) -> None:
        """
        Store a secret in the file.

        :param key: The key for the secret.
        :param secret: The secret to store.
        :raises SecretProviderException: If there is an error writing the secret to the file.
        """
        try:
            current_values = self._parse_collection() or {}
            current_values[key] = secret

            with open(self._namespace, "w") as file:
                for k, v in json.loads(secret).items():
                    file.write(f"{k}={v}\n")
        except Exception as ex:
            message = f"Failed to store secret {key}: {ex}"
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

    def delete(self, key: str) -> None:
        """
        Delete a secret from the file.

        :param key: The key for the secret.
        :raises SecretProviderException: If key is missing or if there is an error deleting the secret.
        """
        if not key:
            message = "delete: key is missing"
            logger.warning(message)
            raise SecretProviderException(message)

        try:
            collection = self._parse_collection()
            
            # Check if key exists in the collection
            if key in collection:
                del collection[key]
                
                # Write the updated collection back to the file
                with open(self._namespace, "w") as file:
                    for k, v in collection.items():
                        file.write(f"{k}={v}\n")
        except Exception as e:
            message = f"Error deleting secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)

