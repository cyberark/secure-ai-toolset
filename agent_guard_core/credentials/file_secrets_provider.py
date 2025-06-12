import os
from typing import Dict, Optional

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

    def __init__(self, namespace: str = ".env"):
        """
        Initialize the FileSecretsProvider with a namespace.

        :param namespace: The namespace to use for storing secrets.
         It can include slashes to represent a directory structure.
        """
        super().__init__()
        if not namespace:
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

    def get_secret_dictionary(self) -> Dict[str, str]:
        """
        Retrieve the secret dictionary from the file.

        :return: A dictionary containing the secrets.
        :raises SecretProviderException: If there is an error reading the secrets from the file.
        """
        secret_dictionary = {}
        try:
            if os.path.exists(self._dictionary_path):
                secret_dictionary = dotenv_values(self._dictionary_path)
            else:
                return {}
        except Exception as e:
            raise SecretProviderException(e) from e

        return secret_dictionary

    def store_secret_dictionary(self, secret_dictionary: Dict):
        """
        Store the secret dictionary to the file.

        :param secret_dictionary: A dictionary containing the secrets to store.
        :raises SecretProviderException: If there is an error writing the secrets to the file.
        """
        dictionary_text = ""
        for key, value in secret_dictionary.items():
            if key:
                dictionary_text += f'{key}={value}\n'
        try:
            with open(self._dictionary_path, "w+") as f:
                f.write(dictionary_text)

        except Exception as e:
            raise SecretProviderException(str(e.args[0]))

    def connect(self) -> bool:
        """
        Simulate a connection to the secrets storage.

        :return: True indicating the connection status.
        """
        return True

    def store(self, key: str, secret: str) -> None:
        """
        Store a secret in the file.

        :param key: The key for the secret.
        :param secret: The secret to store.
        :raises SecretProviderException: If there is an error writing the secret to the file.
        """
        dictionary: Dict = self.get_secret_dictionary()
        dictionary[key] = secret
        self.store_secret_dictionary(dictionary)

    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from the file.

        :param key: The key for the secret.
        :return: The secret if it exists, otherwise None.
        """
        dictionary: Dict = self.get_secret_dictionary()
        return dictionary.get(key)

    def delete(self, key: str) -> None:
        """
        Delete a secret from the file.

        :param key: The key for the secret.
        :raises SecretProviderException: If the key is none or empty.
        """
        if not key:
            self.logger.warning("remove: key is none or empty")
            raise SecretProviderException(
                "delete secret failed, key is none or empty")

        dictionary: Dict = self.get_secret_dictionary()
        if dictionary and key in dictionary:
            del dictionary[key]
            self.store_secret_dictionary(dictionary)
