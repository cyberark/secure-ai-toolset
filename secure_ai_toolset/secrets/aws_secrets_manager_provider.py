import json
from typing import Dict, Optional

import boto3

from .secrets_provider import BaseSecretsProvider, SecretProviderException

SERVICE_NAME = "secretsmanager"
DEFAULT_REGION = "us-east-1"
DEFAULT_NAMESPACE = "default"
DEFAULT_SECRET_ID = "agentic_env_vars"


class AWSSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from AWS Secrets Manager.
    """

    def __init__(self,
                 region_name=DEFAULT_REGION,
                 namespace: Optional[str] = None):
        """
        Initializes the AWS Secrets Manager client with the specified region.
        
        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        """
        super().__init__()
        self._client = None
        self._region_name = region_name
        namespace = DEFAULT_NAMESPACE if namespace is None else namespace
        self._dictionary_path = f"{namespace}/{DEFAULT_SECRET_ID}"

    def connect(self) -> bool:
        """
        Establishes a connection to the AWS Secrets Manager service.
        
        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        :return: Caller identity information if connection is successful.
        """
        if self._client:
            return

        try:
            self._client = boto3.client(SERVICE_NAME,
                                        region_name=self._region_name)
            # Verify connectivity using STS get caller identity
            # caller = boto3.client('sts').get_caller_identity()
            return True

        except Exception as e:
            self.logger.error(
                f"Error initializing AWS Secrets Manager client: {e}")
            raise SecretProviderException(
                message=
                f'Error connecting to the secret provider: AWSSecretsProvider with this exception: {e.args[0]}'
            )

    def get_secret_dictionary(self) -> Optional[Dict]:

        try:
            self.connect()
            response = self._client.get_secret_value(
                SecretId=self._dictionary_path)
            meta = response.get("ResponseMetadata", {})
            if meta.get(
                    "HTTPStatusCode") != 200 or "SecretString" not in response:
                self.logger.error("get: secret retrieval error")
                return None
            secret_text = response["SecretString"]
            if secret_text:
                secret_dict = json.loads(secret_text)
                return secret_dict
            else:
                return {}

        except Exception as e:
            raise SecretProviderException(str(e))

    def store_secret_dictionary(self, secret_dictionary: Dict):
        if not secret_dictionary:
            raise SecretProviderException("Dictionary not provided")

        try:
            self.connect()
            secret_text = json.dumps(secret_dictionary)
            self._client.create_secret(Name=self._dictionary_path,
                                       SecretString=secret_text)

        except self._client.exceptions.ResourceExistsException:
            self._client.put_secret_value(SecretId=self._dictionary_path,
                                          SecretString=secret_text)
        except Exception as e:
            message = f"Error storing secret: {e}"
            self.logger.error(message)
            raise SecretProviderException(message)

    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager. Creates or updates the secret.
        
        :param key: The name of the secret.
        :param secret: The secret value to store.
    
        Caution:
        Concurrent access to secrets can cause issues. If two clients simultaneously list, update different environment variables,
        and then store, one client's updates may override the other's if they are working on the same secret.
        This issue will be addressed in future versions.            
        """
        if not key or not secret:
            self.logger.warning(
                "store: key is missing, proceeding with default")
            return

        dictionary = self.get_secret_dictionary()

        if not dictionary:
            dictionary = {}

        dictionary[key] = secret
        self.store_secret_dictionary(dictionary)

    def get(self, key: str) -> Optional[str]:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        
        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        """
        if not key:
            self.logger.warning("get: key is missing, proceeding with default")

        dictionary = self.get_secret_dictionary()

        if dictionary:
            return dictionary.get(key)

    def delete(self, key: str) -> None:
        """
        Deletes a secret from AWS Secrets Manager by key.
        
        :param key: The name of the secret to delete.
        """
        if not key:
            message = "delete secret failed, key is none or empty"
            self.logger.warning(message)
            raise SecretProviderException(message)

        dictionary = self.get_secret_dictionary()

        if dictionary:
            del dictionary[key]
            self.store_secret_dictionary(dictionary)
