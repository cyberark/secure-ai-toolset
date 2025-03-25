import base64
import json
import os
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider, SecretProviderException

# Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
DEFAULT_TOKEN_EXPIRATION = 8
API_TOKEN_SAFETY_BUFFER = 3
DEFAULT_API_TOKEN_DURATION = DEFAULT_TOKEN_EXPIRATION - API_TOKEN_SAFETY_BUFFER

DEFAULT_REGION = "us-east-1"
DEFAULT_NAMESPACE = "data/default"
DEFAULT_SECRET_ID = "agentic_env_vars"
DEFAULT_CONJUR_ACCOUNT = "conjur"


class ConjurSecretsProvider(BaseSecretsProvider):
    def __init__(self,
                 region_name=DEFAULT_REGION,
                 namespace=DEFAULT_NAMESPACE):
        super().__init__()

        self._url = os.getenv("CONJUR_APPLIANCE_URL")
        self._workload_id = os.getenv("CONJUR_AUTHN_LOGIN")
        self._api_key = os.getenv("CONJUR_AUTHN_API_KEY", "")
        self._authenticator_id = os.getenv("CONJUR_AUTHENTICATOR_ID")
        self._account = os.getenv("CONJUR_ACCOUNT", DEFAULT_CONJUR_ACCOUNT)
        self._region = os.getenv("CONJUR_AUTHN_IAM_REGION", region_name)
        self._access_token = None
        self._access_token_expiration = datetime.now()
        self._branch = namespace
        self._secret_name = DEFAULT_SECRET_ID

    def _authenticate_aws(self) -> bool:
        """
        Authenticates with Conjur using AWS IAM role.

        This function uses AWS IAM credentials to authenticate with Conjur. It signs a request using the STS temporary credentials and then fetches an API token from Conjur.

        Returns:
            bool: True if the authentication succeeded, False if it failed.
        """

        session = boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()

        # Sign the request using the STS temporary credentials
        sigv4 = SigV4Auth(credentials, "sts", self._region)
        sts_uri = f"https://sts.{self._region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
        request = AWSRequest(method="GET", url=sts_uri)
        sigv4.add_auth(request)
        signed_headers = json.dumps(dict(request.headers))

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._url}/{self._authenticator_id}/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {"Accept-Encoding": "base64"}
        response = requests.post(conjur_authenticate_uri,
                                 data=signed_headers,
                                 headers=headers)
        if response.status_code == 200:
            self._access_token = response.text
            return True
        return False

    def _authenticate_api_key(self) -> bool:
        """
        Authenticates with Conjur using an API key.

        Returns:
            bool: True if the authentication succeeded, False if it failed.
        """

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._url}/authn/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {"Accept-Encoding": "base64"}
        response = requests.post(conjur_authenticate_uri,
                                 data=self._api_key,
                                 headers=headers)
        if response.status_code == 200:
            self._access_token = response.text
            return True
        return False

    def _get_conjur_headers(self) -> Dict[str, str]:
        if not self._access_token:
            self.connect()
        headers = {
            'Authorization': f'Token token="{self._access_token}"',
            'Content-Type': 'text/plain'
        }

        return headers

    def _update_token_expiration(self):
        # Attempt to get the expiration from the token. If failing then the default expiration will be used
        try:
            # The token is in JSON format. Each field in the token is base64 encoded.
            # So we decode the payload filed and then extract the expiration date from it
            decoded_token_payload = base64.b64decode(json.loads(self._access_token)['payload'].encode('ascii'))
            token_expiration = json.loads(decoded_token_payload)['exp']
            self._access_token_expiration = datetime.fromtimestamp(token_expiration) - timedelta(minutes=API_TOKEN_SAFETY_BUFFER)
        except:
            # If we can't extract the expiration from the token because we work with an older version
            # of Conjur, then we use the default expiration
            self._access_token_expiration = datetime.now() + timedelta(minutes=DEFAULT_API_TOKEN_DURATION)

    def connect(self) -> bool:
        if not self._access_token or datetime.now() > self._access_token_expiration:
            if not self._authenticator_id:
                return self._authenticate_api_key()
            elif self._authenticator_id.startswith("authn-iam"):
                return self._authenticate_aws()
        return False

    def get_secret_dictionary(self) -> Dict[str, str]:
        """
        Retrieves the secret dictionary from Conjur.

        :return: A dictionary containing the secrets.
        :raises SecretProviderException: If there is an error retrieving the secrets.
        """

        self.connect()
        url = f"{self._url}/secrets/{self._account}/variable/{urllib.parse.quote(f'{self._branch}/{self._secret_name}')}"

        try:
            response = requests.get(url, headers=self._get_conjur_headers())
            if response.status_code == 404:
                return {}
            elif response.status_code != 200:
                self.logger.error(f"get: secret retrieval error: {response.text}")
                raise SecretProviderException(response.text)
            return json.loads(response.text)
        except Exception as e:
            self.logger.error(f"Error retrieving secret: {e}")
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

        self.connect()
        url = f"{self._url}/policies/{self._account}/policy/{urllib.parse.quote(self._branch)}"
        policy_body = f"""
                - !variable
                  id: {self._secret_name}
                """
        try:
            response = requests.post(url,
                                     data=policy_body,
                                     headers=self._get_conjur_headers())
            if response.status_code != 201:
                self.logger.error(f"Error creating secret: {response.text}")
                raise SecretProviderException(f"Error storing secret: {response.text}")

            set_secret_url = f"{self._url}/secrets/conjur/variable/{urllib.parse.quote(f'{self._branch}/{self._secret_name}')}"
            response = requests.post(set_secret_url,
                                     data=json.dumps(secret_dictionary),
                                     headers=self._get_conjur_headers())
            if response.status_code != 201:
                self.logger.error(f"Error storing secret: {response.text}")
                raise SecretProviderException(f"Error storing secret: {response.text}")
        except Exception as e:
            message = f"Error storing secret: {e}"
            self.logger.error(message)
            raise SecretProviderException(message)

    def store(self, key: str, secret: str) -> None:
        """
        Stores a secret in Conjur. Creates or updates the secret.

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
        Deletes a secret from Conjur by key.

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
