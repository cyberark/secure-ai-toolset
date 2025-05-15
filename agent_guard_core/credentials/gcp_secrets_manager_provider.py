import json
from typing import Dict, Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager

from .secrets_provider import BaseSecretsProvider, SecretProviderException

DEFAULT_PROJECT_ID = "default"
DEFAULT_SECRET_ID = "agentic_env_vars"
DEFAULT_SECRET_VERSION = "latest"
DEFAULT_REPLICATION_TYPE = "automatic"
SUPPORTED_REPLICATION_TYPES = ["automatic", "user_managed"]


class GCPSecretsProvider(BaseSecretsProvider):

    def __init__(self,
                 project_id: str = DEFAULT_PROJECT_ID,
                 secret_id: str = DEFAULT_SECRET_ID,
                 secret_id_version: str = DEFAULT_SECRET_VERSION,
                 region: Optional[str] = None,
                 replication_type: str = DEFAULT_REPLICATION_TYPE):
        super().__init__()
        self._project_id = project_id
        self._secret_id = secret_id
        self._secret_id_version = secret_id_version
        self._region = region
        self._client = None

        if replication_type not in SUPPORTED_REPLICATION_TYPES:
            raise SecretProviderException(
                f"Unsupported replication type: {replication_type}. "
                f"Supported types are: {', '.join(SUPPORTED_REPLICATION_TYPES)}"
            )
        self._replication_type = replication_type

    def connect(self) -> bool:
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
        return f"{self._get_secret_path()}/versions/{self._secret_id_version}"

    def _get_secret_parent(self) -> str:
        return f"projects/{self._project_id}"

    def get_secret_dictionary(self) -> Dict[str, str]:
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
        if not secret_dictionary:
            raise SecretProviderException("Empty secret dictionary provided")

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
        if not key or not secret:
            raise SecretProviderException("store: key or secret is missing")

        secret_dict = self.get_secret_dictionary()
        secret_dict[key] = secret
        self.store_secret_dictionary(secret_dict)

    def get(self, key: str) -> Optional[str]:
        if not key:
            self.logger.warning("get: key is missing")
            return None

        secret_dict = self.get_secret_dictionary()
        return secret_dict.get(key)

    def delete(self, key: str) -> None:
        if not key:
            raise SecretProviderException("delete: key is missing")

        secret_dict = self.get_secret_dictionary()
        if key in secret_dict:
            del secret_dict[key]
            self.store_secret_dictionary(secret_dict)
