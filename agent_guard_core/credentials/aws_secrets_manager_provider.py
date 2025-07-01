import json
from typing import Dict, Optional, Union

import boto3

import logging

logging.getLogger("botocore").setLevel(logging.CRITICAL)

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

from .secrets_provider import BaseSecretsProvider, SecretProviderException

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

    def get(self, key: str) -> Optional[Union[str, Dict[str, str]]]:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        
        If namespace is provided, gets the secret as a key in the namespace collection.
        Otherwise, gets the secret directly by its key.
        
        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        :raises SecretProviderException: If there is an error retrieving the secret.
        """
        if not key:
            message = "get: key is missing"
            self.logger.warning(message)
            raise SecretProviderException(message)
            
        # Determine which secret ID to use
        secret_id = self._namespace if self._namespace else key
        
        # Get the raw secret string
        secret_text = self._get_raw_secret(secret_id)
        if not secret_text:
            return None
            
        # If we have a namespace, parse the JSON and get the specific key
        if self._namespace:
            try:
                secrets_dict = json.loads(secret_text)
                if isinstance(secrets_dict, dict):
                    return secrets_dict.get(key)
                else:
                    message = f"get: Expected JSON object in namespace {self._namespace}, got: {type(secrets_dict)}"
                    self.logger.warning(message)
                    return None
            except json.JSONDecodeError as e:
                message = f"get: Failed to parse JSON from namespace {self._namespace}: {str(e)}"
                self.logger.warning(message)
                return None
        else:
            # For direct secret access, try to parse as JSON first
            try:
                return json.loads(secret_text)
            except json.JSONDecodeError:
                # If not valid JSON, return as string
                return secret_text

    def _update_namespace_collection(self, update_function):
        """
        Helper method to update a collection in a namespace.
        
        :param update_function: Function that updates the collection dictionary
        :raises SecretProviderException: If there is an error updating the collection
        """
        if not self._namespace:
            raise SecretProviderException("_update_namespace_collection: namespace is not set")
            
        # Get current collection
        raw_secret = self._get_raw_secret(self._namespace)
        collection = {}
        
        if raw_secret:
            try:
                collection = json.loads(raw_secret)
                if not isinstance(collection, dict):
                    collection = {}
            except json.JSONDecodeError:
                # If not valid JSON, start with empty dict
                collection = {}
                
        # Apply the update
        update_function(collection)
        
        # Store the updated collection
        secret_string = json.dumps(collection)
        try:
            # Try to create the secret first
            try:
                self._client.create_secret(Name=self._namespace, SecretString=secret_string)
            except self._client.exceptions.ResourceExistsException:
                # If it already exists, update it
                self._client.put_secret_value(SecretId=self._namespace, SecretString=secret_string)
        except Exception as e:
            message = f"Error updating namespace collection: {str(e)}"
            self.logger.error(message)
            raise SecretProviderException(message)

    def store(self, key: str, secret: Union[str, Dict[str, str]]) -> None:
        """
        Stores a secret in AWS Secrets Manager.
        
        If namespace is provided, stores the secret as a key in the namespace collection.
        Otherwise, stores the secret directly with its key as the SecretId.
        
        :param key: The name of the secret key.
        :param secret: The secret value to store (string or dictionary).
        :raises SecretProviderException: If key or secret is missing or if there is an error storing the secret.
        """
        if not key or secret is None:
            message = "store: key or secret is missing"
            self.logger.warning(message)
            raise SecretProviderException(message)

        try:
            self.connect()
            
            # Handle namespace-based storage
            if self._namespace:
                def update_collection(collection):
                    collection[key] = secret
                    
                self._update_namespace_collection(update_collection)
            else:
                # Direct secret storage
                secret_string = secret
                if isinstance(secret, dict):
                    secret_string = json.dumps(secret)
                
                try:
                    self._client.create_secret(Name=key, SecretString=secret_string)
                except self._client.exceptions.ResourceExistsException:
                    self._client.put_secret_value(SecretId=key, SecretString=secret_string)
                    
        except Exception as e:
            message = f"Error storing secret: {str(e)}"
            self.logger.error(message)
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
            self.logger.warning(message)
            raise SecretProviderException(message)

        try:
            self.connect()
            
            # Handle namespace-based deletion
            if self._namespace:
                # Get existing secrets in the namespace
                raw_secret = self._get_raw_secret(self._namespace)
                if not raw_secret:
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