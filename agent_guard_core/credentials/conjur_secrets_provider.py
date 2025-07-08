""" Defines utility class ConjurSecretsProvider for authenticating to Conjur & retrieving secrets """

import base64
import json
import logging
import os
import urllib.parse
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Dict, Optional

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from dotenv import load_dotenv

from agent_guard_core.credentials.enum import ConjurEnvVars, CredentialsProvider
from agent_guard_core.credentials.secrets_provider import (BaseSecretsProvider, SecretProviderException,
                                                           secrets_provider_fm)

# Tokens should only be reused for 5 minutes (max lifetime is 8 minutes)
DEFAULT_TOKEN_EXPIRATION = 8
API_TOKEN_SAFETY_BUFFER = 3
DEFAULT_API_TOKEN_DURATION = DEFAULT_TOKEN_EXPIRATION - API_TOKEN_SAFETY_BUFFER

DEFAULT_REGION = "us-east-1"
DEFAULT_CONJUR_ACCOUNT = "conjur"

HTTP_TIMEOUT_SECS = 2.0

logger = logging.getLogger(__name__)


@secrets_provider_fm.flavor(CredentialsProvider.CONJUR)
class ConjurSecretsProvider(BaseSecretsProvider):
    """
    Manages storing and retrieving secrets from Conjur.
    """

    def __init__(self,
                 namespace: Optional[str] = None,
                 ext_authn_cred_provider=None,
                 **kwargs):
        """
        Initializes the Conjur Secrets Provider.

        :param namespace: Optional namespace for the secrets. Defaults to None.
        :param ext_authn_cred_provider: Optional external authentication credential provider.
        """
        super().__init__(namespace, **kwargs)
        load_dotenv()

        # reference to external authn credential provider function
        self._ext_authn_cred_provider = ext_authn_cred_provider

        init_error = False
        # common authn values for all authn endpoints
        self._url = os.getenv(ConjurEnvVars.CONJUR_APPLIANCE_URL, None)
        if self._url is None:
            logger.error("ConjurSecretsProvider:__init__(): Required env var CONJUR_APPLIANCE_URL is missing.")
            init_error = True

        self._authenticator_id = os.getenv(ConjurEnvVars.CONJUR_AUTHENTICATOR_ID, None)
        if self._authenticator_id is None:
            logger.error("ConjurSecretsProvider:__init__(): Required env var CONJUR_AUTHENTICATOR_ID is missing.")
            init_error = True

        self._workload_id = os.getenv(ConjurEnvVars.CONJUR_AUTHN_LOGIN, None)
        if self._workload_id is None:
            logger.error("ConjurSecretsProvider:__init__(): Required env var CONJUR_AUTHN_LOGIN is missing.")
            init_error = True

        if init_error:
            raise SecretProviderException(
                "ConjurSecretsProvider: One or more required environment variables are missing."
            )

        self._account = os.getenv(ConjurEnvVars.CONJUR_ACCOUNT, DEFAULT_CONJUR_ACCOUNT)
        self._branch = namespace

        # Define private vars initialized elsewhere
        self._access_token = None
        self._access_token_expiration = datetime.now()
        self._region = None

    # ---- AWS authentication ----
    def _authenticate_aws_iam(self) -> bool:
        """
        Authenticates with Conjur using AWS IAM role.

        This function uses AWS IAM credentials to authenticate with
        Conjur. It signs a request using the STS temporary credentials
        and then fetches an API token from Conjur.

        Returns:
            bool: True if the authentication succeeded, False if it failed.
        """

        session = boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()
        if credentials is None:
            logger.error(
                "ConjurSecretsProvider:_authenticate_aws_iam(): Error getting AWS IAM credentials."
            )
            raise SecretProviderException(
                "ConjurSecretsProvider:_authenticate_aws_iam(): Error getting AWS IAM credentials."
            )

        # Sign the request using the STS temporary credentials
        self._region = os.getenv(ConjurEnvVars.CONJUR_AUTHN_IAM_REGION, DEFAULT_REGION)
        sigv4 = SigV4Auth(credentials, "sts", self._region)
        sts_uri = f"https://sts.{self._region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15"
        request = AWSRequest(method="GET", url=sts_uri)
        sigv4.add_auth(request)
        signed_headers = json.dumps(dict(request.headers))

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._url}/{self._authenticator_id}/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {"Accept-Encoding": "base64"}
        response = requests.post(
            conjur_authenticate_uri,
            data=signed_headers,
            headers=headers,
            timeout=HTTP_TIMEOUT_SECS,
        )
        if response.status_code == HTTPStatus.OK:
            self._access_token = response.text
            return True
        return False

    # ---- API key authentication ----
    def _authenticate_api_key(self) -> bool:
        """
        Authenticates with Conjur using an API key.

        Returns:
            bool: True if the authentication succeeded, False if it failed.
        """

        if self._ext_authn_cred_provider is not None:
            logger.debug(
                "ConjurSecretsProvider:_authenticate_api_key(): Calling external credential provider function..."
            )
            api_key = self._ext_authn_cred_provider()
        else:
            api_key = os.getenv(ConjurEnvVars.CONJUR_AUTHN_API_KEY, None)
            if api_key is None:
                logger.error(
                    "ConjurSecretsProvider:_authenticate_api_key(): Required env var CONJUR_AUTHN_API_KEY is missing."
                )
        if api_key is None:
            logger.error(
                "ConjurSecretsProvider:_authenticate_api_key(): No API key provided."
            )
            raise SecretProviderException(
                "ConjurSecretsProvider:_authenticate_api_key(): No API key provided."
            )

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._url}/authn/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {"Accept-Encoding": "base64"}
        response = requests.post(
            conjur_authenticate_uri,
            data=api_key,
            headers=headers,
            timeout=HTTP_TIMEOUT_SECS,
        )
        if response.status_code == HTTPStatus.OK:
            self._access_token = response.text
            return True
        return False

    # ---- JWT authentication ----
    def _authenticate_jwt(self) -> bool:
        """
        Authenticates with Conjur using a JSON web token (JWT).

        Default behavior is the JWT is expected to be in an environment
        variable named CONJUR_AUTHN_JWT. As the JWT may expire if it has a
        short TTL, the default behavior is intended for dev/test only.

        The intention is the user should define an external function that
        returns a current JWT per the operating environment. A reference to
        the provider function should be passed at instance creation.

        Returns:
            bool: True if the authentication succeeded, False if it failed.
        """

        if self._ext_authn_cred_provider is not None:
            logger.debug(
                "ConjurSecretsProvider:_authenticate_jwt(): Calling external credential provider function..."
            )
            local_jwt = self._ext_authn_cred_provider()
        else:
            local_jwt = os.getenv(ConjurEnvVars.CONJUR_AUTHN_JWT, None)
            if local_jwt is None:
                logger.error(
                    "ConjurSecretsProvider:_authenticate_jwt(): Required env var CONJUR_AUTHN_JWT is missing."
                )
        if local_jwt is None:
            logger.error(
                "ConjurSecretsProvider:_authenticate_jwt(): No JWT provided.")
            raise SecretProviderException(
                "ConjurSecretsProvider:_authenticate_jwt(): No JWT provided.")

        # Fetch an access token from Conjur
        conjur_authenticate_uri = (
            f"{self._url}/{self._authenticator_id}/{self._account}/authenticate"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "base64",
        }
        response = requests.post(
            conjur_authenticate_uri,
            data=f"jwt={local_jwt}",
            headers=headers,
            timeout=HTTP_TIMEOUT_SECS,
        )
        if response.status_code == HTTPStatus.OK:
            self._access_token = response.text
            return True

        logger.error(
            "ConjurSecretsProvider:_authenticate_jwt(): authentication error: %s",
            response.text,
        )
        return False

    def _get_conjur_headers(self) -> Dict[str, str]:
        self.connect()
        headers = {
            "Authorization": f'Token token="{self._access_token}"',
            "Content-Type": "text/plain",
        }
        return headers

    def _update_token_expiration(self):
        # Attempt to get the expiration from the token. If failing then the default expiration will be used
        try:
            # The token is in JSON format. Each field in the token is base64 encoded.
            # So we decode the payload filed and then extract the expiration date from it
            decoded_token_payload = base64.b64decode(
                json.loads(self._access_token)["payload"].encode("ascii"))
            token_expiration = json.loads(decoded_token_payload)["exp"]
            self._access_token_expiration = datetime.fromtimestamp(
                token_expiration) - timedelta(minutes=API_TOKEN_SAFETY_BUFFER)
        except:
            # If we can't extract the expiration from the token because we work with an older version
            # of Conjur, then we use the default expiration
            self._access_token_expiration = datetime.now() + timedelta(
                minutes=DEFAULT_API_TOKEN_DURATION)

    def connect(self) -> bool:
        """
        Establishes a connection to the Conjur service.

        :return: True if connection is successful, False otherwise.
        :raises SecretProviderException: If unable to determine authentication method.
        """
        if not self._access_token or datetime.now() > self._access_token_expiration:
            if self._authenticator_id.startswith("authn-jwt"):
                return self._authenticate_jwt()
            if self._authenticator_id.startswith("authn-iam"):
                return self._authenticate_aws_iam()
            if not self._authenticator_id or self._authenticator_id.startswith("authn-api"):
                return self._authenticate_api_key()
            message = f"connect(): Unable to determine authentication method from authenticator ID: {self._authenticator_id}"
            logger.error(message)
            raise SecretProviderException(message)
        return True

    def _get(self, key: str) -> Optional[str]:
        """
        Internal method to retrieve raw secret value from Conjur.

        :param key: The ID of the secret to retrieve
        :return: The raw secret string or None if not found
        :raises SecretProviderException: If there is an error retrieving the secret
        """
        try:
            self.connect()
            url = f"{self._url}/secrets/{self._account}/variable/{urllib.parse.quote(key)}"
            
            response = requests.get(
                url,
                headers=self._get_conjur_headers(),
                timeout=HTTP_TIMEOUT_SECS,
            )
            if response.status_code == HTTPStatus.NOT_FOUND:
                logger.warning(f"Secret {key}: not found or has empty value.")
                return None
            if response.status_code != HTTPStatus.OK:
                logger.error(f"_get: secret retrieval error: {response.text}")
                raise SecretProviderException(response.text)
            return response.text
        except Exception as e:
            logger.error(f"Error retrieving secret: {e}")
            raise SecretProviderException(str(e))

