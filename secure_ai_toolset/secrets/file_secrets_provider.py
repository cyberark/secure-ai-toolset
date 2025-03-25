import os
from typing import Dict, Optional

from dotenv import dotenv_values

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider, SecretProviderException

DEFAULT_NAMESPACE = ""
DEFAULT_SECRET_ID = ".env"


class FileSecretsProvider(BaseSecretsProvider):
    """
    FileSecretsProvider is a class that implements the BaseSecretsProvider interface.
    It provides methods to store, retrieve, and delete secrets in a file-based storage.
    """

    def __init__(self, namespace: str = None):
        """
        Initialize the FileSecretsProvider with an optional namespace.

        :param namespace: The namespace to use for storing secrets. Defaults to an empty string.
        """
        super().__init__()
        self._namespace = DEFAULT_NAMESPACE if not namespace else namespace
        self._dictionary_path = f"{self._namespace}{DEFAULT_SECRET_ID}"

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
            raise SecretProviderException(str(e))

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
            raise SecretProviderException(str(e))

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
