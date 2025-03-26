"""
Secrets Provider module.
"""

# this is a abstract class for secrets provider
import abc
import logging
from typing import Dict, Optional


class SecretProviderException(Exception):
    """
    Exception class for secrets provider errors.
    """

    def __init__(self, message: str):
        super().__init__(message)


class BaseSecretsProvider(abc.ABC):
    """
    Base class for secrets providers.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the BaseSecretsProvider with optional arguments.
        """
        self.logger = logging.getLogger(__name__)

    @abc.abstractmethod
    def connect(self) -> bool:
        """
        Establish a connection to the secrets storage.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """

    @abc.abstractmethod
    def store(self, key: str, secret: str) -> None:
        """
        Store a secret in the storage.

        Args:
            key (str): The key under which the secret will be stored.
            secret (str): The secret to be stored.
        """

    @abc.abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Retrieve a secret from the storage.

        Args:
            key (str): The key of the secret to retrieve.

        Returns:
            Optional[str]: The secret if found, otherwise None.
        """

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """
        Delete a secret from the storage.

        Args:
            key (str): The key of the secret to delete.
        """

    @abc.abstractmethod
    def get_secret_dictionary(self) -> Dict[str, str]:
        """
        Retrieve all secrets as a dictionary.

        Returns:
            Dict[str, str]: A dictionary containing all secrets.
        """

    @abc.abstractmethod
    def store_secret_dictionary(self, secret_dictionary: Dict):
        """
        Store multiple secrets from a dictionary.

        Args:
            secret_dictionary (Dict): A dictionary containing secrets to store.
        """
