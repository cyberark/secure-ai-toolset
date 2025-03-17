import json
import logging
import os
from typing import Dict

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider

DEFAULT_ENV_VARS_NAMESPACE = "default"
ENV_VARS_DEFAULT_SECRET_ID = "agentic_env_vars"


class EnvironmentVariablesManager:

    def __init__(self,
                 secret_provider: BaseSecretsProvider,
                 namespace: str = DEFAULT_ENV_VARS_NAMESPACE,
                 env_var_secret_id: str = ENV_VARS_DEFAULT_SECRET_ID):
        """
        Initialize the EnvironmentVariablesManager with a secret provider, namespace, and secret ID.
        
        :param secret_provider: The secret provider to use for storing and retrieving secrets.
        :param namespace: The context in which the secret containing the environment variables will be stored.
        :param env_var_secret_name: The name of the secret, in the given namespace, in which the environment variables will be stored.
        """
        self.secret_provider = secret_provider
        self._namespace = namespace
        self._secret_dictionary_key = f"{namespace}/{env_var_secret_id}"
        self._secret_dict = {}
        self._logger = logging.getLogger(__name__)

    def list_env_vars(self) -> Dict[str, str]:
        """
        List all environment variables stored in the secret provider.
        
        :return: A dictionary of environment variables.
        """
        try:
            secret_dict_text = self.secret_provider.get(
                key=self._secret_dictionary_key)
            if not secret_dict_text:
                self._secret_dict = {}
            else:
                self._secret_dict = json.loads(secret_dict_text)
        except Exception as e:
            self._logger.warning(e)
            return {}
        return self._secret_dict

    def add_env_var(self, key: str, value: str):
        """
        Add a new environment variable to the secret provider.
        
        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        self.set_env_var(key, value)

    def get_env_var(self, key: str) -> str:
        """
        Retrieve an environment variable from the secret provider.
        
        :param key: The key of the environment variable.
        :return: The value of the environment variable.
        """
        return self.list_env_vars().get(key)

    def set_env_var(self, key: str, value: str):
        """
        Set an environment variable in the secret provider.
        
        :param key: The key of the environment variable.
        :param value: The value of the environment variable.
        """
        try:
            self._secret_dict = self.list_env_vars()
            if not self._secret_dict:
                self._secret_dict = {}
            self._secret_dict[key] = value
            secrets_text = json.dumps(self._secret_dict)
            self.secret_provider.store(key=self._secret_dictionary_key,
                                       secret=secrets_text)
        except Exception as e:
            self._logger.error(e)

    def remove_env_var(self, key: str):
        """
        Remove an environment variable from the secret provider.
        
        :param key: The key of the environment variable to remove.
        """
        try:
            self._secret_dict = self.list_env_vars()
            if key in self._secret_dict:
                del self._secret_dict[key]
                self.secret_provider.store(key=self._secret_dictionary_key,
                                           secret=json.dumps(
                                               self._secret_dict))
        except Exception as e:
            self._logger.error(e)

    def populate_env_vars(self):
        """
        Populate environment variables from the secret provider into the system environment.
        """
        env_vars = self.list_env_vars()
        for key, value in env_vars.items():
            os.environ[key] = value

    def depopulate_env_vars(self):
        """
        Remove environment variables from the system environment.
        """
        env_vars = self.list_env_vars()
        for key in env_vars.keys():
            if key in os.environ:
                del os.environ[key]
