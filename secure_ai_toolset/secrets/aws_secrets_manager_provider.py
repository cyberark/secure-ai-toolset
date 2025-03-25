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
        :param namespace: Optional namespace for the secrets. Defaults to 'default'.
        """
        super().__init__()
        self._client = None
        self._region_name = region_name
        namespace = DEFAULT_NAMESPACE if not namespace else namespace
        self._dictionary_path = f"{namespace}/{DEFAULT_SECRET_ID}"

    def connect(self) -> bool:
        """
        Establishes a connection to the AWS Secrets Manager service.
        
        :return: True if connection is successful, raises SecretProviderException otherwise.
        """
        if self._client:
            return True

        try:
            self._client = boto3.client(SERVICE_NAME,
                                        region_name=self._region_name)
            return True

        except Exception as e:
            self.logger.error(
                f"Error initializing AWS Secrets Manager client: {e}")
            raise SecretProviderException(
                message=
                f'Error connecting to the secret provider: AWSSecretsProvider with this exception: {e.args[0]}'
            )

    def get_secret_dictionary(self) -> Dict[str, str]:
        """
        Retrieves the secret dictionary from AWS Secrets Manager.
        
        :return: A dictionary containing the secrets.
        :raises SecretProviderException: If there is an error retrieving the secrets.
        """
        try:
            self.connect()
            response = self._client.get_secret_value(
                SecretId=self._dictionary_path)
            meta = response.get("ResponseMetadata", {})
            if meta.get(
                    "HTTPStatusCode") != 200 or "SecretString" not in response:
                message = "get: secret retrieval error"
                self.logger.error(message)
                raise SecretProviderException(message)
            secret_text = response["SecretString"]
            if secret_text:
                secret_dict = json.loads(secret_text)
                return secret_dict
            else:
                return {}

        except self._client.exceptions.ResourceNotFoundException as e:
            return {}

        except Exception as e:
            raise SecretProviderException(str(e))

    def store_secret_dictionary(self, secret_dictionary: Dict):
        """
        Stores the secret dictionary in AWS Secrets Manager.
        
        :param secret_dictionary: The dictionary containing secrets to store.
        :raises SecretProviderException: If there is an error storing the secrets.
        """
        # an empty dictionary is valid, yet a none one is not and raises an exception
        if secret_dictionary is None:
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
        :raises SecretProviderException: If key or secret is missing, or if there is an error storing the secret.
    
        Caution:
        Concurrent access to secrets can cause issues. If two clients simultaneously list, update different environment variables,
        and then store, one client's updates may override the other's if they are working on the same secret.
        This issue will be addressed in future versions.            
        """
        if not key or not secret:
            message = "store: key or secret is missing"
            self.logger.warning(message)
            raise SecretProviderException(message)

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
        :raises SecretProviderException: If there is an error retrieving the secret.
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
        :raises SecretProviderException: If key is missing or if there is an error deleting the secret.
        """
        if not key:
            message = "delete secret failed, key is none or empty"
            self.logger.warning(message)
            raise SecretProviderException(message)

        dictionary = self.get_secret_dictionary()

        if dictionary:
            del dictionary[key]
            self.store_secret_dictionary(dictionary)
