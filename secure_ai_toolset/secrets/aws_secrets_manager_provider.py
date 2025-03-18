import boto3

from .secrets_provider import BaseSecretsProvider

DEFAULT_REGION = "us-east-1"
SERVICE_NAME = "secretsmanager"


class AWSSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from AWS Secrets Manager.
    """

    def __init__(self, region_name=DEFAULT_REGION):
        """
        Initializes the AWS Secrets Manager client with the specified region.
        
        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        """
        super().__init__()
        self._client = None

    def connect(self, region_name=DEFAULT_REGION):
        """
        Establishes a connection to the AWS Secrets Manager service.
        
        :param region_name: AWS region name where the secrets manager is located. Defaults to 'us-east-1'.
        :return: Caller identity information if connection is successful.
        """
        if self._client:
            return

        try:
            self._client = boto3.client(SERVICE_NAME, region_name=region_name)
            # Verify connectivity using STS get caller identity
            caller = boto3.client('sts').get_caller_identity()
            return caller

        except Exception as e:
            self.logger.error(
                f"Error initializing AWS Secrets Manager client: {e}")
            raise

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
            self.logger.warning("store: key or secret is missing")
            return

        try:
            self.connect()
            self._client.create_secret(Name=key, SecretString=secret)
        except self._client.exceptions.ResourceExistsException:
            self._client.put_secret_value(SecretId=key, SecretString=secret)
        except Exception as e:
            self.logger.error(f"Error storing secret: {e}")
            return

    def get(self, key: str) -> str:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        
        :param key: The name of the secret to retrieve.
        :return: The secret value if retrieval is successful, None otherwise.
        """
        if not key:
            self.logger.warning("get: key is missing")
            return None
        try:
            self.connect()
            response = self._client.get_secret_value(SecretId=key)
            meta = response.get("ResponseMetadata", {})
            if meta.get(
                    "HTTPStatusCode") != 200 or "SecretString" not in response:
                self.logger.error("get: secret retrieval error")
                return None
            return response["SecretString"]
        except self._client.exceptions.ResourceNotFoundException:
            self.logger.error("Secret not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving secret: {e}")
            return None

    def delete(self, key: str) -> None:
        """
        Deletes a secret from AWS Secrets Manager by key.
        
        :param key: The name of the secret to delete.
        """
        if not key:
            self.logger.warning("delete: key is missing")
            return
        try:
            self.connect()
            self._client.delete_secret(SecretId=key,
                                       ForceDeleteWithoutRecovery=True)
        except self._client.exceptions.ResourceNotFoundException:
            self.logger.error("Secret not found.")
        except Exception as e:
            self.logger.error(f"Error deleting secret: {e}")
