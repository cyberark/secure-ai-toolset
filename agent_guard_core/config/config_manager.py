import os
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional, Union

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider

logger = logging.getLogger(__name__)

# Default configuration file name
DEFAULT_CONFIG_FILE = "config.env"

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

    def __init__(self, config_file_path: Optional[Union[str, Path]] = None):
        """
        Initialize the ConfigManager with a file-based secrets provider.
        
        Args:
            config_file_path: Optional custom path to the configuration file.
                If not provided, defaults to ~/.agent_guard/config.env
        """
        # Create the config directory if it doesn't exist
        config_dir = Path.joinpath(Path.home(), '.agent_guard')
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided config file path or default
        if config_file_path:
            if isinstance(config_file_path, str):
                self._config_file_path = Path(config_file_path)
            else:
                self._config_file_path = config_file_path
        else:
            self._config_file_path = Path.joinpath(config_dir, DEFAULT_CONFIG_FILE)
        
        # Convert to string for compatibility
        file_path_str = str(self._config_file_path)
        
        # Create the parent directories if they don't exist
        os.makedirs(os.path.dirname(file_path_str), exist_ok=True)
        
        # Create an empty file if it doesn't exist
        if not os.path.exists(file_path_str):
            try:
                with open(file_path_str, "w") as f:
                    pass  # Create an empty file
            except Exception as e:
                logger.warning(f"Could not create config file: {e}")
        
        self._config_provider = FileSecretsProvider(namespace=file_path_str)
        
    def get_config(self) -> Dict[str, str]:
        """
        Get the current configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration key-value pairs
        """
        try:
            # Use the provider's parse_collection method to get all config values
            return self._config_provider._parse_collection() or {}
        except Exception as e:
            logger.warning(f"Error getting config: {e}")
            return {}

    def set_config_value(self, key: str, value: str) -> None:
        """
        Set a specific key to a value in the config file.
        
        Args:
            key: Configuration key to set
            value: Value to assign to the key
            
        Raises:
            ValueError: If key is empty
        """
        if not key:
            raise ValueError("Configuration key cannot be empty")
        
        try:
            self._config_provider.store(key, value)
        except Exception as e:
            logger.error(f"Error setting config value {key}: {e}")
            raise

    def get_config_value(self, key: str) -> Optional[str]:
        """
        Get a specific value for a key from the config file.
        
        Args:
            key: Configuration key to retrieve
            
        Returns:
            Configuration value if found, None otherwise
        """
        if not key:
            return None
            
        try:
            return self._config_provider.get(key)
        except Exception as e:
            logger.debug(f"Config value not found for key {key}: {e}")
            return None
            
    @property
    def config_file_path(self) -> Path:
        """
        Get the path to the configuration file.
        
        Returns:
            Path object representing the configuration file path
        """
        return self._config_file_path
