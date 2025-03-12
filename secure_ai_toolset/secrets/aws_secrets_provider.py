from .secrets_provider import BaseSecretsProvider
import boto3

DEFAULT_REGION = "us-east-1"
SERVICE_NAME = "secretsmanager"

class AWSSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from AWS Secrets Manager.
    """    
    def __init__(self, region_name=DEFAULT_REGION):
        """
        Initializes the AWS Secrets Manager client with the specified region.
        """
        super().__init__()
        self.client = None

    def connect(self, region_name = DEFAULT_REGION):
        if self.client:
            return

        try:
            self.client = boto3.client(SERVICE_NAME, region_name=region_name)
            return self.client
            
        except Exception as e:
            self.logger.error(f"Error initializing AWS Secrets Manager client: {e}")
            raise

    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in AWS Secrets Manager. Creates or updates the secret.
        """
        if not key or not secret:
            # log error
            self.logger.warning("store: key or secret is missing")
            return
        try:
            self.connect()
            self.client.create_secret(Name=key, SecretString=secret)
        except self.client.exceptions.ResourceExistsException:
            self.client.put_secret_value(SecretId=key, SecretString=secret)
        except Exception as e:
            self.logger.error(f"Error storing secret: {e}")
            return

    def get(self, key: str) -> str:
        """
        Retrieves a secret from AWS Secrets Manager by key.
        Returns None if the key is missing or retrieval fails.
        """
        if not key:
            # log error
            return None
        try:
            self.connect()
            response = self.client.get_secret_value(SecretId=key)
            meta = response.get("ResponseMetadata", {})
            if meta.get("HTTPStatusCode") != 200 or "SecretString" not in response:
                # log error
                return None
            return response["SecretString"]
        except self.client.exceptions.ResourceNotFoundException:
            self.logger.error("Secret not found.")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving secret: {e}")
            return None

    def delete(self, key: str) -> None:
        """
        Deletes a secret from AWS Secrets Manager by key.
        """
        if not key:
            # log error
            self.logger.warning("delete: key is missing")
            return
        try:
            self.connect()
            self.client.delete_secret(SecretId=key, ForceDeleteWithoutRecovery=True)
        except self.client.exceptions.ResourceNotFoundException:
            self.logger.error("Secret not found.")
        except Exception as e:
            self.logger.error(f"Error deleting secret: {e}")

