import os
import json
import logging
from typing import Any, Optional, Dict, OrderedDict

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
    
    This provider uses a .env file for storage. The namespace parameter specifies the path
    to the file where secrets will be stored.
    """

    def __init__(self, namespace: Optional[str] = ".env", **kwargs: Any) -> None:
        """
        Initialize the FileSecretsProvider with a namespace.

        :param namespace: The file path where secrets will be stored.
         It can include slashes to represent a directory structure.
        """
        super().__init__(namespace, **kwargs)

        if namespace is None:
            raise SecretProviderException("Namespace cannot be empty")

        # Use namespace as directory structure, last part as file name
        base_path, file_name = os.path.split(namespace)
        if not file_name:
            raise SecretProviderException("Namespace must include a file name")

        if base_path and not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        # Convert relative paths to absolute
        self.file_path = os.path.abspath(namespace)

        # Check if the file exists, if not, create it
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, "w"):
                    pass  # Create an empty file
            except Exception as e:
                raise SecretProviderException(
                    f"Failed to create secrets file: {e}")

    def connect(self) -> bool:
        """
        Simulate a connection to the secrets storage.

        :return: True indicating the connection status.
        """
        return True

    def _parse_collection(self) -> Dict[str, str]:
        """
        Parse the dotenv file and return its contents as a dictionary.
        
        :return: Dictionary containing the key-value pairs from the dotenv file
        :raises SecretProviderException: If there is an error reading or parsing the file
        """
        try:
            if not os.path.exists(self.file_path):
                return {}
                
            collection = dotenv_values(self.file_path)
            if collection is None:
                collection = {}
                
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

            with open(self.file_path, "w") as file:
                for k, v in current_values.items():
                    file.write(f"{k}={v}\n")
        except Exception as ex:
            message = f"Failed to store secret {key}: {ex}"
            logger.error(message)
            raise SecretProviderException(message)

    def _get(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from the file.

        :param key: The key for the secret.
        :return: The secret if it exists, otherwise None.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        try:
            collection = self._parse_collection()
            return collection.get(key)
        except Exception as e:
            message = f"Error retrieving secret: {str(e)}"
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
            # Check if we're working with a namespace
            if self._namespace is not None:
                # Get the namespace collection
                collection_raw = self._get_raw_secret(key=self._namespace)
                if collection_raw:
                    try:
                        collection = json.loads(collection_raw)
                        if key in collection:
                            del collection[key]
                            # Store the updated collection back
                            self._store(self._namespace, json.dumps(collection))
                    except json.JSONDecodeError as e:
                        message = f"Failed to parse JSON from namespace {self._namespace}: {str(e)}"
                        logger.error(message)
                        raise SecretProviderException(message)
            else:
                # Direct key-value storage
                collection = self._parse_collection()
                if key in collection:
                    del collection[key]
                    # Write the updated collection back to the file
                    with open(self.file_path, "w") as file:
                        for k, v in collection.items():
                            file.write(f"{k}={v}\n")
        except Exception as e:
            message = f"Error deleting secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)

