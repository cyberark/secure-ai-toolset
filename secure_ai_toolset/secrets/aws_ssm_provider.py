import boto3
from botocore.exceptions import ClientError
from pydantic import SecretStr
from .secrets_provider import BaseSecretsProvider

class AWSParameterStoreProvider(BaseSecretsProvider):

    def __init__(self, region_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ssm_client = boto3.client('ssm', region_name=region_name)

    def connect(self) -> str:
        try:
            self.ssm_client.describe_parameters()
            return "Connected to AWS Systems Manager Parameter Store"
        except ClientError as e:
            self.logger.error(f"Failed to connect: {e}")
            return "Failed to connect"

    def store(self, key: str, secret: str) -> None:
        try:
            self.ssm_client.put_parameter(
                Name=key,
                Value=secret,
                Type='SecureString',
                Overwrite=True
            )
            self.logger.info(f"Secret stored successfully: {key}")
        except ClientError as e:
            self.logger.error(f"Failed to store secret: {e}")

    def get(self, key: str) -> SecretStr:
        try:
            response = self.ssm_client.get_parameter(
                Name=key,
                WithDecryption=True
            )
            secret = response['Parameter']['Value']
            self.logger.info(f"Secret retrieved successfully: {key}")
            return SecretStr(secret)
        except ClientError as e:
            self.logger.error(f"Failed to retrieve secret: {e}")
            return SecretStr("")

    def delete(self, key: str) -> str:
        try:
            self.ssm_client.delete_parameter(Name=key)
            self.logger.info(f"Secret deleted successfully: {key}")
            return "Secret deleted successfully"
        except ClientError as e:
            self.logger.error(f"Failed to delete secret: {e}")
            return "Failed to delete secret"
