import json
from typing import Dict, Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager
from google.cloud.secretmanager_v1 import AddSecretVersionRequest, SecretPayload

from .secrets_provider import BaseSecretsProvider, SecretProviderException

DEFAULT_PROJECT_ID = "default"
DEFAULT_SECRET_ID = "agentic_env_vars"
DEFAULT_SECRET_VERSION = "latest"


class GCPSecretsProvider(BaseSecretsProvider):

    def __init__(self,
                 project_id: str = DEFAULT_PROJECT_ID,
                 secret_id: str = DEFAULT_SECRET_ID,
                 secret_id_version: str = DEFAULT_SECRET_VERSION,
                 region: Optional[str] = None):
        super().__init__()
        self._project_id = project_id
        self._secret_id = secret_id
        self._secret_id_version = secret_id_version
        self._region = region
        self._client = None

    def connect(self) -> bool:
        if self._client:
            return True
        try:
            self._client = secretmanager.SecretManagerServiceClient()
            return True
        except Exception as e:
            self.logger.error(f"Error initializing Secret Manager client: {e}")
            raise SecretProviderException(
                f"GCP Secret Manager init failed: {e}")

    def _get_secret_path(self) -> str:
        if self._region:
            return f"projects/{self._project_id}/secrets/{self._secret_id}/locations/{self._region}"
        return f"projects/{self._project_id}/secrets/{self._secret_id}"

    def _get_version_path(self) -> str:
        return f"{self._get_secret_path()}/versions/{self._secret_id_version}"

    def _get_secret_parent(self) -> str:
        return f"projects/{self._project_id}"

    def get_secret_dictionary(self) -> Dict[str, str]:
        self.connect()
        try:
            version_path = self._get_version_path()
            request = secretmanager.AccessSecretVersionRequest(
                name=version_path)
            response = self._client.access_secret_version(request=request)
            secret_text = response.payload.data.decode("utf-8")
            return json.loads(secret_text)
        except NotFound:
            self.logger.warning("Secret not found: %s", self._secret_id)
            return {}
        except Exception as e:
            self.logger.error(f"Failed to retrieve secret: {e}")
            raise SecretProviderException(f"Error retrieving secret: {e}")

    def store_secret_dictionary(self, secret_dictionary: Dict[str,
                                                              str]) -> None:
        if not secret_dictionary:
            raise SecretProviderException("Empty secret dictionary provided")

        self.connect()
        secret_text = json.dumps(secret_dictionary)
        parent = self._get_secret_parent()

        try:
            request = secretmanager.CreateSecretRequest(
                parent=parent,
                secret_id=self._secret_id,
                secret=secret_text,
            )
            self._client.create_secret(request=request)
        except AlreadyExists:
            pass  # Secret already exists
        except Exception as e:
            self.logger.error(f"Failed to create secret: {e}")
            raise SecretProviderException(f"Error creating secret: {e}")

        # Add a version to the secret
        try:
            request = AddSecretVersionRequest(
                parent=self._get_secret_path(),
                payload=SecretPayload(data=secret_text.encode("utf-8")))
            self._client.add_secret_version(request=request)
        except Exception as e:
            self.logger.error(f"Failed to add secret version: {e}")
            raise SecretProviderException(f"Error storing secret: {e}")

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
