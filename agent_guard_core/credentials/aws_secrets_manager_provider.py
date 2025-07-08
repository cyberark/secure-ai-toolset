import json
import logging
from typing import Any, Optional

import boto3

logging.getLogger("botocore").setLevel(logging.CRITICAL)

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

from .secrets_provider import BaseSecretsProvider, SecretProviderException

SERVICE_NAME = "secretsmanager"
DEFAULT_REGION = "us-east-1"

logger = logging.getLogger(__name__)

@secrets_provider_fm.flavor(CredentialsProvider.AWS_SECRETS_MANAGER)
class AWSSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from AWS Secrets Manager.
    """

    def __init__(self, namespace: Optional[str] = None, region_name: str = DEFAULT_REGION, **kwargs: Any):
        """
        Initializes the AWS Secrets Manager client with the specified region.

        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        :param namespace: Optional namespace for the secrets. Defaults to None.
        """
        super().__init__(namespace, **kwargs)
        self._client: Optional[Any] = None
        self._region_name = region_name

    def connect(self) -> bool:
        """
        Establishes a connection to the AWS Secrets Manager service.

        :return: True if connection is successful, raises SecretProviderException otherwise.
        """
        if self._client is not None:
            return True

        try:
            self._client = boto3.client(service_name=SERVICE_NAME, region_name=self._region_name)
            return True

        except Exception as e:
            logger.error("Error initializing AWS Secrets Manager client: %s", str(e))
            raise SecretProviderException(
                message=f"Error connecting to the secret provider: AWSSecretsProvider with this exception: {str(e)}"
            )

    def _get(self, key: str) -> Optional[str]:
        """
        Internal method to retrieve raw secret value from AWS Secrets Manager.
        
        :param secret_id: The ID of the secret to retrieve
        :return: The raw secret string or None if not found
        :raises SecretProviderException: If there is an error retrieving the secret
        """
        try:
            self.connect()
            response = self._client.get_secret_value(SecretId=key)  # type: ignore
            
            meta = response.get("ResponseMetadata", {})
            if meta.get("HTTPStatusCode") != 200 or "SecretString" not in response:
                message = f"_get_raw_secret: secret retrieval error for ID {key}"
                logger.error(message)
                raise SecretProviderException(message)
                
            return str(response["SecretString"])
        
        except self._client.exceptions.ResourceNotFoundException:  # type: ignore
            logger.warning(f"Secret not found: {key}")
            return None
        except Exception as e:
            message = f"Error retrieving secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)
