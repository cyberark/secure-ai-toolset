import gc
import logging
import os
from typing import Awaitable, Callable, Dict, Optional

from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider

"""
The EnvironmentVariablesManager class provides functionality for storing,
retrieving, and deleting environment variables in a secrets provider. It also
has methods for populating and depopulating OS environment variables based on
the stored secrets. Use set_env_vars decorator to seamlessly manage environment
variables around function execution.

Caveats
   * When secrets are populated and depopulated, we delete their references from the garbage collector.
     However, Python strings are immutable, so an old copy persists in memory.
     Advanced techniques such as memory dumps can reveal them.
   * When setting a new secret key, bear in mind it can override an existing environment variable with the same name.
     Avoid overriding system variables such as PATH, SHELL, only if you are sure of what you are doing.
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
        """
        self.secret_provider: BaseSecretsProvider = secret_provider
        self._logger: logging.Logger = logging.getLogger(__name__)

    def __enter__(self):
        """
        Context manager entry method: populates environment variables into the system.

        :return: The EnvironmentVariablesManager instance.
        """
        self.populate_env_vars()
        return self

    def __exit__(self, exc_type: Optional[type],
                 exc_val: Optional[BaseException], exc_tb: Optional[object]):
        """
        Context manager exit method: removes environment variables from the system.

        :param exc_type: The exception type, if any.
        :param exc_val: The exception value, if any.
        :param exc_tb: The traceback object, if any.
        """
        self.depopulate_env_vars()

    def list_env_vars(self) -> Dict[str, str]:
        """
        List all environment variables stored in the secret provider.

        :return: A dictionary of environment variables.
        """
        try:
            secret_dictionary = self.secret_provider.get_secret_dictionary()
        except Exception as e:
            self._logger.warning("Failed to list environment variables: %s",
                                 e.args[0])
            return {}
        return secret_dictionary

    def add_env_var(self, key: str, value: str) -> None:
        """
        Add a new environment variable to the secret provider.

        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        self._set_env_var(key, value)

    def get_env_var(self, key: str) -> Optional[str]:
        """
        Retrieve an environment variable from the secret provider.

        :param key: The key of the environment variable.
        :return: The value of the environment variable, or None if not found.
        """
        secret_dictionary: Dict[str, str] = self.list_env_vars()
        secret_value: Optional[str] = secret_dictionary.get(key)

        # Clear the secret dictionary from process references
        del secret_dictionary
        gc.collect()

        return secret_value

    def _set_env_var(self, key: str, value: str) -> None:
        """
        Set an environment variable in the secret provider.

        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        try:
            secret_dictionary: Dict[
                str, str] = self.secret_provider.get_secret_dictionary()
            secret_dictionary[key.strip()] = value.strip()
            self.secret_provider.store_secret_dictionary(
                secret_dictionary=secret_dictionary)
        except Exception as e:
            self._logger.error("Failed to set environment variable '%s': %s",
                               key, e.args[0])
        finally:
            # Clear the secret dictionary from process references
            del secret_dictionary
            gc.collect()

    def _remove_env_var(self, key: str) -> None:
        """
        Remove an environment variable from the secret provider.

        :param key: The key of the environment variable to remove.
        """
        try:
            secret_dictionary: Dict[
                str, str] = self.secret_provider.get_secret_dictionary()
            if key in secret_dictionary:
                del secret_dictionary[key]
                self.secret_provider.store_secret_dictionary(
                    secret_dictionary=secret_dictionary)
        except Exception as e:
            self._logger.error(
                "Failed to remove environment variable '%s': %s", key,
                e.args[0])
        finally:
            # Clear the secret dictionary from process references
            del secret_dictionary
            gc.collect()

    def populate_env_vars(self) -> None:
        """
        Populate environment variables from the secret provider into the system environment.
        """
        env_vars: Dict[str, str] = self.list_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value
            self._logger.info("Populating environment variable with key: %s",
                              key)
            del value

        # Clear the secret dictionary from process references
        del env_vars
        gc.collect()

    def depopulate_env_vars(self) -> None:
        """
        Remove environment variables from the system environment.
        """
        env_vars: Dict[str, str] = self.list_env_vars()
        for key in env_vars.keys():
            if key in os.environ:
                del os.environ[key]
                self._logger.info("Removing environment variable with key: %s",
                                  key)

        # Clear the secret dictionary from process references
        del env_vars
        gc.collect()

    @staticmethod
    def set_env_vars(
        secret_provider: BaseSecretsProvider
    ) -> Callable[[Callable[..., Awaitable]], Callable[..., Awaitable]]:
        """
        Decorator that populates environment variables from the given secret
        provider before the wrapped function is called, and depopulates them
        afterwards. This ensures that any environment variables needed for the
        function are ready before execution and cleaned up afterward.

        :param secret_provider: The secret provider to use for managing environment variables.
        :return: A decorator for asynchronous functions.
        """

        def async_decorator(
                func: Callable[..., Awaitable]) -> Callable[..., Awaitable]:

            async def wrapper(*args, **kwargs) -> Awaitable:
                env_var_mgr = EnvironmentVariablesManager(
                    secret_provider=secret_provider)
                env_var_mgr.populate_env_vars()

                try:
                    result = await func(*args, **kwargs)
                finally:
                    env_var_mgr.depopulate_env_vars()

                return result

            return wrapper

        return async_decorator
