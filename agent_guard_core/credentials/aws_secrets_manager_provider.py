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
        self._namespace = namespace

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

    def _get(self, secret_id: str) -> Optional[str]:
        """
        Internal method to retrieve raw secret value from AWS Secrets Manager.
        
        :param secret_id: The ID of the secret to retrieve
        :return: The raw secret string or None if not found
        :raises SecretProviderException: If there is an error retrieving the secret
        """
        try:
            self.connect()
            response = self._client.get_secret_value(SecretId=secret_id)  # type: ignore
            
            meta = response.get("ResponseMetadata", {})
            if meta.get("HTTPStatusCode") != 200 or "SecretString" not in response:
                message = f"_get_raw_secret: secret retrieval error for ID {secret_id}"
                logger.error(message)
                raise SecretProviderException(message)
                
            return str(response["SecretString"])
        
        except self._client.exceptions.ResourceNotFoundException:  # type: ignore
            logger.warning(f"Secret not found: {secret_id}")
            return None
        except Exception as e:
            message = f"Error retrieving secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)


    def _store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager.
        
        :param key: The name of the secret key.
        :param secret: The secret value to store (string or dict).
        :raises SecretProviderException: If key or secret is missing or if there is an error storing the secret.
        """
        
        try:
            self.connect()
            self._client.create_secret(Name=key, SecretString=secret)  # type: ignore
        except self._client.exceptions.ResourceExistsException:  # type: ignore
            self._client.put_secret_value(SecretId=key, SecretString=secret)  # type: ignore
        except Exception as e:
            message = f"Error storing secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)
    

    def delete(self, key: str) -> None:
        """
        Deletes a secret from AWS Secrets Manager.
        
        If namespace is provided, removes the key from the namespace collection.
        Otherwise, deletes the secret directly by its key.
        
        :param key: The name of the secret to delete.
        :raises SecretProviderException: If key is missing or if there is an error deleting the secret.
        """
        if not key:
            message = "delete: key is missing"
            logger.warning(message)
            raise SecretProviderException(message)

        try:
            self.connect()
            
            # Handle namespace-based deletion
            if self._namespace:
                # Get existing secrets in the namespace
                raw_secret = self._get(self._namespace)
                if raw_secret is None:
                    return  # Namespace doesn't exist, nothing to delete
                    
                try:
                    secrets_dict = json.loads(raw_secret)
                    if not isinstance(secrets_dict, dict):
                        return  # Not a dictionary, can't delete key
                        
                    # If key exists in dictionary, remove it and update
                    if key in secrets_dict:
                        del secrets_dict[key]
                        
                        # Store the updated dictionary
                        secret_string = json.dumps(secrets_dict)
                        self._client.put_secret_value(SecretId=self._namespace, SecretString=secret_string)  # type: ignore
                except json.JSONDecodeError:
                    # Not valid JSON, can't delete a key
                    return
            else:
                # Direct secret deletion
                try:
                    self._client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)  # type: ignore
                except self._client.exceptions.ResourceNotFoundException:  # type: ignore
                    # Secret doesn't exist, nothing to delete
                    return
                    
        except Exception as e:
            message = f"Error deleting secret: {str(e)}"
            logger.error(message)
            raise SecretProviderException(message)