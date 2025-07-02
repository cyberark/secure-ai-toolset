import json
import logging
from typing import Any, Dict, Optional, Union

import boto3

logging.getLogger("botocore").setLevel(logging.CRITICAL)

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

from .secrets_provider import BaseSecretsProvider, SecretNotFoundException, SecretProviderException

SERVICE_NAME = "secretsmanager"
DEFAULT_REGION = "us-east-1"


@secrets_provider_fm.flavor(CredentialsProvider.AWS_SECRETS_MANAGER)
class AWSSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from AWS Secrets Manager.
    """

    def __init__(self, region_name=DEFAULT_REGION, namespace: Optional[str] = None):
        """
        Initializes the AWS Secrets Manager client with the specified region.

        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        :param namespace: Optional namespace for the secrets. Defaults to None.
        """
        super().__init__()
        self._client = None
        self._region_name = region_name
        self._namespace = namespace

    def connect(self) -> bool:
        """
        Establishes a connection to the AWS Secrets Manager service.

        :return: True if connection is successful, raises SecretProviderException otherwise.
        """
        if self._client:
            return True

        try:
            self._client = boto3.client(SERVICE_NAME, region_name=self._region_name)
            return True

        except Exception as e:
            self.logger.error("Error initializing AWS Secrets Manager client: %s", str(e))
            raise SecretProviderException(
                message=f"Error connecting to the secret provider: AWSSecretsProvider with this exception: {str(e)}"
            )

    def _get_raw_secret(self, secret_id: str) -> Optional[str]:
        """
        Internal method to retrieve raw secret value from AWS Secrets Manager.
        
        :param secret_id: The ID of the secret to retrieve
        :return: The raw secret string or None if not found
        :raises SecretProviderException: If there is an error retrieving the secret
        """
        try:
            self.connect()
            response = self._client.get_secret_value(SecretId=secret_id)
            
            meta = response.get("ResponseMetadata", {})
            if meta.get("HTTPStatusCode") != 200 or "SecretString" not in response:
                message = f"_get_raw_secret: secret retrieval error for ID {secret_id}"
                self.logger.error(message)
                raise SecretProviderException(message)
                
            return response["SecretString"]
        
        except self._client.exceptions.ResourceNotFoundException:
            self.logger.warning(f"Secret not found: {secret_id}")
            return None
        except Exception as e:
            message = f"Error retrieving secret: {str(e)}"
            self.logger.error(message)
            raise SecretProviderException(message)

    def get(self, key: str) -> str:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        
        If namespace is provided, gets the secret as a key in the namespace collection.
        Otherwise, gets the secret directly by its key.
        
        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        # Determine which secret ID to use
        secret_id = self._namespace or key
        
        # Get the raw secret string
        secret_text = self._get_raw_secret(secret_id)
        if secret_text is None:
            raise SecretNotFoundException(key)
            
        if self._namespace is None:
            return secret_text
        
        try:
            secrets_dict = json.loads(secret_text)
            if isinstance(secrets_dict, dict):
                return secrets_dict.get(key)
            else:
                message = f"get: Expected JSON object in namespace {self._namespace}, got: {type(secrets_dict)}"
                self.logger.warning(message)
                raise SecretProviderException(message)
        except json.JSONDecodeError as e:
            message = f"get: Failed to parse JSON from namespace {self._namespace}: {str(e)}"
            self.logger.warning(message)
            return None

    def _store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager.
        
        :param key: The name of the secret key.
        :param secret: The secret value to store (string or dict).
        :raises SecretProviderException: If key or secret is missing or if there is an error storing the secret.
        """
        
        try:
            self.connect()
            self._client.create_secret(Name=key, SecretString=secret)
        except self._client.exceptions.ResourceExistsException:
            self._client.put_secret_value(SecretId=key, SecretString=secret)
        except Exception as e:
            message = f"Error storing secret: {str(e)}"
            self.logger.error(message)
            raise SecretProviderException(message)
        
    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager.
        
        If namespace is provided, stores the secret as a key in the namespace collection.
        Otherwise, stores the secret directly with its key as the SecretId.
        
        :param key: The name of the secret key.
        :param secret: The secret value to store (string).
        :raises SecretProviderException: If key or secret is missing or if there is an error storing the secret.
        """

        if self._namespace:
            collection = self._get_raw_secret(self._namespace) or {}
            collection[key] = secret
            secret = json.dumps(collection)
            key = self._namespace
        
        self._store(key, secret)

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
            self.logger.warning(message)
            raise SecretProviderException(message)

        try:
            self.connect()
            
            # Handle namespace-based deletion
            if self._namespace:
                # Get existing secrets in the namespace
                raw_secret = self._get_raw_secret(self._namespace)
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
                        self._client.put_secret_value(SecretId=self._namespace, SecretString=secret_string)
                except json.JSONDecodeError:
                    # Not valid JSON, can't delete a key
                    return
            else:
                # Direct secret deletion
                try:
                    self._client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
                except self._client.exceptions.ResourceNotFoundException:
                    # Secret doesn't exist, nothing to delete
                    return
                    
        except Exception as e:
            message = f"Error deleting secret: {str(e)}"
            self.logger.error(message)
            raise SecretProviderException(message)