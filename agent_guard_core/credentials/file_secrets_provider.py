import os
from typing import Any, Optional

from dotenv import dotenv_values

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import (BaseSecretsProvider, SecretProviderException,
                                                           secrets_provider_fm)


@secrets_provider_fm.flavor(CredentialsProvider.FILE_DOTENV)
class FileSecretsProvider(BaseSecretsProvider):
    """
    FileSecretsProvider is a class that implements the BaseSecretsProvider interface.
    It provides methods to store, retrieve, and delete secrets in a file-based storage.
    """

    def __init__(self, namespace: str = ".env", **kwargs: Any) -> None:
        """
        Initialize the FileSecretsProvider with a namespace.

        :param namespace: The namespace to use for storing secrets.
         It can include slashes to represent a directory structure.
        """
        super().__init__()

        if namespace is None:
            raise SecretProviderException("Namespace cannot be empty")

        # Use namespace as directory structure, last part as file name
        base_path, file_name = os.path.split(namespace)
        if not file_name:
            raise SecretProviderException("Namespace must include a file name")

        if base_path and not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        self._dictionary_path = os.path.abspath(
            os.path.join(base_path, file_name))

        # Check if the file exists, if not, create it
        if not os.path.exists(self._dictionary_path):
            try:

                with open(self._dictionary_path, "w"):
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

    def _store(self, key: str, secret: str) -> None:
        """
        Store a secret in the file.

        :param key: The key for the secret.
        :param secret: The secret to store.
        :raises SecretProviderException: If there is an error writing the secret to the file.
        """
        current_values = dotenv_values(self._dictionary_path) or {}
        current_values[key] = secret

        try:
            with open(self._dictionary_path, "w") as file:
                for k, v in current_values.items():
                    file.write(f"{k}={v}\n")
        except Exception as ex:
            raise SecretProviderException(
                f"Failed to store secret {key}: {ex}")

    def _get(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from the file.

        :param key: The key for the secret.
        :return: The secret if it exists, otherwise None.
        """
        collection: dict[str, Any] = dotenv_values(self._dictionary_path)
        return collection.get(key)

    def delete(self, key: str) -> None:
        """
        Delete a secret from the file.

        :param key: The key for the secret.
        """

        collection: dict[str, Any] = dotenv_values(self._dictionary_path)
        if key in collection:
            del collection[key]
            with open(self._dictionary_path, "w") as file:
                for k, v in collection.items():
                    file.write(f"{k}={v}\n")

