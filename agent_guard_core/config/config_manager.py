from enum import Enum
from pathlib import Path

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider



class BasicEnum(Enum):

    @classmethod
    def get_keys(cls):
        """
        Return a list of all secret provider keys (enum names).
        """
        return [member.name for member in cls]

    @classmethod
    def get_default(cls):
        """
        Return the default enum value. by default its the first item
        """
        return cls.get_keys()[0]


class ConfigurationOptions(BasicEnum):
    """
    Enum for configuration keys used by Agent Guard.
    """
    SECRET_PROVIDER = "The secret provider that Agent Guard is configured to use"
    CONJUR_AUTHN_LOGIN = "The ID of the workload that authenticates to Conjur"
    CONJUR_APPLIANCE_URL = "The endpoint URL of Conjur"
    CONJUR_AUTHN_API_KEY = "The API Key to authenticate in the cloud"
    TARGET_MCP_SERVER_CONFIG_FILE = "The MCP server endpoint that Agent Guard connects to"

class ConfigManager:
    """
    Manages Agent Guard configuration using a file-based secrets provider.
    """

    def __init__(self):
        self._config_file_path = Path.joinpath(Path.home(), '.agent_guard',
                                               'config.env')
        self._config_provider = FileSecretsProvider(
            namespace=self._config_file_path)
        self._config_dictionary = self._config_provider.get_secret_dictionary()

    def get_config(self):
        """
        Get the current configuration as a dictionary.
        """
        return self._config_dictionary

    def set_config_value(self, key, value):
        """
        Set a specific key to a value in the config file.
        """
        self._config_dictionary[key] = value
        self._config_provider.store_secret_dictionary(self._config_dictionary)

    def get_config_value(self, key):
        """
        Get a specific value for a key from the config file.
        """
        return self._config_dictionary.get(key)
