import json
from typing import Dict, Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

from .secrets_provider import BaseSecretsProvider, SecretProviderException

DEFAULT_PROJECT_ID = "default"
DEFAULT_SECRET_ID = "agentic_env_vars"
DEFAULT_SECRET_VERSION = "latest"
DEFAULT_REPLICATION_TYPE = "automatic"
SUPPORTED_REPLICATION_TYPES = ["automatic", "user_managed"]


@secrets_provider_fm.flavor(CredentialsProvider.GCP_SECRETS_MANAGER)
class GCPSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from Google Cloud Secret Manager.
    """

    def __init__(self,
                 project_id: str = DEFAULT_PROJECT_ID,
                 secret_id: str = DEFAULT_SECRET_ID,
                 region: Optional[str] = None,
                 replication_type: str = DEFAULT_REPLICATION_TYPE):
        """
        Initializes the GCP Secret Manager client with the specified configuration.

        :param project_id: GCP project ID where the secret manager is located. Defaults to 'default'.
        :param secret_id: The secret ID to use. Defaults to 'agentic_env_vars'.
        :param region: Optional region for the secret. Defaults to None.
        :param replication_type: Replication type for the secret. Defaults to 'automatic'.
        :raises SecretProviderException: If the replication type is not supported.
        """
        super().__init__()
        self._project_id = project_id
        self._secret_id = secret_id
        self._region = region
        self._client = None

        if replication_type not in SUPPORTED_REPLICATION_TYPES:
            raise SecretProviderException(
                f"Unsupported replication type: {replication_type}. "
                f"Supported types are: {', '.join(SUPPORTED_REPLICATION_TYPES)}"
            )
        self._replication_type = replication_type

    def connect(self) -> bool:
        """
        Establishes a connection to the GCP Secret Manager service.

        :return: True if connection is successful, raises SecretProviderException otherwise.
        :raises SecretProviderException: If there is an error initializing the client.
        """
        if self._client:
            return True
        try:
            self._client = secretmanager.SecretManagerServiceClient()
            return True
        except Exception as e:
            self.logger.error("Error initializing Secret Manager client: %s",
                              e)
            raise SecretProviderException(
                f"GCP Secret Manager init failed: {e}") from e

    def _get_secret_path(self) -> str:
        if self._region is not None:
            return f"projects/{self._project_id}/locations/{self._region}/secrets/{self._secret_id}"
        return f"projects/{self._project_id}/secrets/{self._secret_id}"

    def _get_version_path(self) -> str:
        return f"{self._get_secret_path()}/versions/{DEFAULT_SECRET_VERSION}"

    def _get_secret_parent(self) -> str:
        return f"projects/{self._project_id}"

    def get_secret_dictionary(self) -> Dict[str, str]:
        """
        Retrieves the secret dictionary from GCP Secret Manager.

        :return: A dictionary containing the secrets.
        :raises SecretProviderException: If there is an error retrieving the secrets.
        """
        self.connect()
        try:
            version_path = self._get_version_path()
            response = self._client.access_secret_version(
                request={"name": version_path})
            secret_text = response.payload.data.decode("utf-8")
            return json.loads(secret_text)
        except NotFound:
            self.logger.warning("Secret not found: %s", self._secret_id)
            return {}
        except Exception as e:
            self.logger.error("Failed to retrieve secret:%s", e)
            raise SecretProviderException(
                f"Error retrieving secret: {e}") from e

    def store_secret_dictionary(self, secret_dictionary: Dict[str,
                                                              str]) -> None:
        """
        Stores the secret dictionary in GCP Secret Manager.

        :param secret_dictionary: The dictionary containing secrets to store.
        :raises SecretProviderException: If the dictionary is None or if there is an error storing the secrets.
        """
        if secret_dictionary is None:
            raise SecretProviderException("Dictionary not provided")

        self.connect()
        secret_text = json.dumps(secret_dictionary)
        try:
            replication_config = {self._replication_type: {}}
            if self._replication_type == "user_managed" and self._region:
                replication_config = {
                    "user_managed": {
                        "replicas": [{
                            "location": self._region
                        }]
                    }
                }

            self._client.create_secret(
                request={
                    "parent": self._get_secret_parent(),
                    "secret_id": self._secret_id,
                    "secret": {
                        "replication": replication_config
                    }
                })
        except AlreadyExists:
            pass  # Secret already exists
        except Exception as e:
            self.logger.error("Failed to create secret:%s", e)
            raise SecretProviderException(f"Error creating secret:{e}") from e

        # Add a version to the secret
        try:
            self._client.add_secret_version(
                request={
                    "parent": self._get_secret_path(),
                    "payload": {
                        "data": secret_text.encode("utf-8")
                    }
                })
        except Exception as e:
            self.logger.error("Failed to add secret version:%s", e)
            raise SecretProviderException(f"Error storing secret:{e}") from e

    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in GCP Secret Manager. Creates or updates the secret.

        :param key: The name of the secret.
        :param secret: The secret value to store.
        :raises SecretProviderException: If key or secret is missing, or if there is an error storing the secret.
        """
        if not key or not secret:
            raise SecretProviderException("store: key or secret is missing")

        secret_dict = self.get_secret_dictionary()
        secret_dict[key] = secret
        self.store_secret_dictionary(secret_dict)

    def get(self, key: str) -> Optional[str]:
        """
        Retrieves a secret from GCP Secret Manager by key.

        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        """
        if not key:
            self.logger.warning("get: key is missing")
            return None

        secret_dict = self.get_secret_dictionary()
        return secret_dict.get(key)

    def delete(self, key: str) -> None:
        """
        Deletes a secret from GCP Secret Manager by key.

        :param key: The name of the secret to delete.
        :raises SecretProviderException: If key is missing or if there is an error deleting the secret.
        """
        if not key:
            raise SecretProviderException("delete: key is missing")

        secret_dict = self.get_secret_dictionary()
        if key in secret_dict:
            del secret_dict[key]
            self.store_secret_dictionary(secret_dict)
