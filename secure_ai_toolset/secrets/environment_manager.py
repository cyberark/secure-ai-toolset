import logging
import os
from typing import Dict

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider

"""
The EnvironmentVariablesManager class provides functionality for storing,
retrieving, and deleting environment variables in a secrets provider. It also
has methods for populating and depopulating OS environment variables based on
the stored secrets. Use set_env_vars decorator to seamlessly manage environment
variables around function execution.
"""


class EnvironmentVariablesManager:
    """
    Manages environment variables using a secrets provider. 
    It enables setting, retrieving, and removing environment variables, 
    as well as populating and depopulating them from the OS environment.
    """

    def __init__(self, secret_provider: BaseSecretsProvider):
        """
        Initialize the EnvironmentVariablesManager.

        :param secret_provider: The secret provider to use for storing and retrieving secrets.
        :param env_var_secret_id: The ID of the secret within for the environment variables.
        """
        self.secret_provider = secret_provider
        self._secret_dict = {}
        self._logger = logging.getLogger(__name__)

    def __enter__(self):
        """
        Context manager entry method: populates environment variables into the system.
        """
        self.populate_env_vars()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit method: removes environment variables from the system.
        """
        self.depopulate_env_vars()

    def list_env_vars(self) -> Dict[str, str]:
        """
        List all environment variables stored in the secret provider.
        
        :return: A dictionary of environment variables.
        """
        try:
            self._secret_dict = self.secret_provider.get_secret_dictionary()
        except Exception as e:
            self._logger.warning(e)
            return {}
        return self._secret_dict

    def _add_env_var(self, key: str, value: str):
        """
        Add a new environment variable to the secret provider.
        
        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        self._set_env_var(key, value)

    def _get_env_var(self, key: str) -> str:
        """
        Retrieve an environment variable from the secret provider.
        
        :param key: The key of the environment variable.
        :return: The value of the environment variable.
        """
        return self.list_env_vars().get(key)

    def _set_env_var(self, key: str, value: str):
        """
        Set an environment variable in the secret provider.
        
        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        try:
            self._secret_dict = self.secret_provider.get_secret_dictionary()

            if not self._secret_dict:
                self._secret_dict = {}

            self._secret_dict[key.strip()] = value.strip()

            self.secret_provider.store_secret_dictionary(
                secret_dictionary=self._secret_dict)

        except Exception as e:
            self._logger.error(e)

    def _remove_env_var(self, key: str):
        """
        Remove an environment variable from the secret provider.
        
        :param key: The key of the environment variable to remove.
        """
        try:
            self._secret_dict = self.secret_provider.get_secret_dictionary()
            if key in self._secret_dict:
                del self._secret_dict[key]
                self.secret_provider.store_secret_dictionary(
                    secret_dictionary=self._secret_dict)

        except Exception as e:
            self._logger.error(e)

    def populate_env_vars(self):
        """
        Populate environment variables from the secret provider into the system environment.
        """
        env_vars = self.list_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value
            self._logger.info(f'populating env var with key:{key}')

    def depopulate_env_vars(self):
        """
        Remove environment variables from the system environment.
        """
        env_vars = self.list_env_vars()
        for key in env_vars.keys():
            if key in os.environ:
                del os.environ[key]
                self._logger.info(
                    f'removing from memory env var with key:{key}')

    @staticmethod
    def set_env_vars(secret_provider: BaseSecretsProvider):
        """
        Decorator that populates environment variables from the given secret
        provider before the wrapped function is called, and depopulates them
        afterwards. This ensures that any environment variables needed for the
        function are ready before execution and cleaned up afterward."
        """

        def async_decorator(func):

            async def wrapper(*args, **kwargs):

                env_var_mgr = EnvironmentVariablesManager(
                    secret_provider=secret_provider)
                env_var_mgr.populate_env_vars()

                result = await func(*args, **kwargs)

                env_var_mgr.depopulate_env_vars()
                return result

            return wrapper

        return async_decorator
