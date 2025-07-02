import json
import logging
from typing import Any, Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

from .secrets_provider import BaseSecretsProvider, SecretProviderException

DEFAULT_PROJECT_ID = "default"
DEFAULT_SECRET_VERSION = "latest"
DEFAULT_REPLICATION_TYPE = "automatic"
SUPPORTED_REPLICATION_TYPES = ["automatic", "user_managed"]

logger = logging.getLogger(__name__)

@secrets_provider_fm.flavor(CredentialsProvider.GCP_SECRETS_MANAGER)
class GCPSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from Google Cloud Secret Manager.
    """

    def __init__(self,
                 namespace: Optional[str] = None,
                 project_id: str = DEFAULT_PROJECT_ID,
                 region: Optional[str] = None,
                 replication_type: str = DEFAULT_REPLICATION_TYPE,
                 **kwargs: Any):
        """
        Initializes the GCP Secret Manager client with the specified configuration.

        :param project_id: GCP project ID where the secret manager is located. Defaults to 'default'.
        :param region: Optional region for the secret. Defaults to None.
        :param replication_type: Replication type for the secret. Defaults to 'automatic'.
        :raises SecretProviderException: If the replication type is not supported.
        """
        super().__init__(namespace)
        self._project_id = project_id
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
            self._client = secretmanager.SecretManagerServiceClient()  # type: ignore
            return True
        except Exception as e:
            logger.error("Error initializing Secret Manager client: %s",
                              e)
            raise SecretProviderException(
                f"GCP Secret Manager init failed: {e}") from e

    def _get_secret_path(self, key: str) -> str:
        if self._region is not None:
            return f"projects/{self._project_id}/locations/{self._region}/secrets/{key}"
        return f"projects/{self._project_id}/secrets/{key}"

    def _get_version_path(self, key: str) -> str:
        return f"{self._get_secret_path(key)}/versions/{DEFAULT_SECRET_VERSION}"

    def _get_secret_parent(self) -> str:
        return f"projects/{self._project_id}"

    def _get(self, key: str) -> Optional[str]:
        self.connect()
        try:
            version_path = self._get_version_path(key)
            response = self._client.access_secret_version(  # type: ignore
                request={"name": version_path})
            secret_text: str = response.payload.data.decode("utf-8")
            return secret_text
        except NotFound:
            logger.warning("Secret not found: %s", key)
            return None
        except Exception as e:
            logger.error("Failed to retrieve secret:%s", e)
            raise SecretProviderException(
                f"Error retrieving secret: {e}") from e

    def _store(self, key: str, secret: str) -> None:
        self.connect()

        try:
            replication_config: dict[str, Any] = {self._replication_type: {}}
            if self._replication_type == "user_managed" and self._region:
                replication_config = {
                    "user_managed": {
                        "replicas": [{
                            "location": self._region
                        }]
                    }
                }

            self._client.create_secret(  # type: ignore
                request={
                    "parent": self._get_secret_parent(),
                    "secret_id": key,
                    "secret": {
                        "replication": replication_config
                    }
                })
        except AlreadyExists:
            pass  # Secret already exists
        except Exception as e:
            logger.error("Failed to create secret:%s", e)
            raise SecretProviderException(f"Error creating secret:{e}") from e

        # Add a version to the secret
        try:
            self._client.add_secret_version(  # type: ignore
                request={
                    "parent": self._get_secret_path(key),
                    "payload": {
                        "data": secret.encode("utf-8")
                    }
                })
        except Exception as e:
            logger.error("Failed to add secret version:%s", e)
            raise SecretProviderException(f"Error storing secret:{e}") from e

    def delete(self, key: str) -> None:
        """
        Deletes a secret from GCP Secret Manager.

        :param key: The name of the secret to delete.
        :raises SecretProviderException: If there is an error deleting the secret.
        """
        self.connect()
        try:
            if self._namespace is None:
                secret_path = self._get_secret_path(key)
                self._client.delete_secret(request={"name": secret_path})  # type: ignore
                logger.info("Deleted secret: %s", key)
                return
            
            collection_raw = self._get(self._namespace)
            # Nothing to delete
            if collection_raw is None:
                return
            collection = json.loads(collection_raw)
            if key in collection:
                del collection[key]
                # Update the namespace with the modified collection
                self._store(self._namespace, json.dumps(collection))
                logger.info("Deleted key '%s' from namespace '%s'", key, self._namespace)
        
        except NotFound:
            logger.warning("Secret not found for deletion: %s", key)
        except Exception as e:
            logger.error("Failed to delete secret:%s", e)
            raise SecretProviderException(f"Error deleting secret:{e}") from e
