import json
import os
import urllib.parse
from typing import Tuple, Optional

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


class ConjurSecretsProvider(BaseSecretsProvider):
    def __init__(self):
        super().__init__()

        self._url = os.getenv("CONJUR_APPLIANCE_URL")
        self._workload_id = os.getenv("CONJUR_AUTHN_LOGIN")
        self._api_key = os.getenv("CONJUR_AUTHN_API_KEY", "")
        self._authenticator_id = os.getenv("CONJUR_AUTHENTICATOR_ID")
        self._account = os.getenv("CONJUR_ACCOUNT", "conjur")
        self._region = os.getenv("CONJUR_AUTHN_IAM_REGION", "us-east-1")
        self._access_token = None

    def _authenticate_aws(self):
        """
        Authenticates with Conjur using AWS IAM role.

        This function uses AWS IAM credentials to authenticate with Conjur. It signs a request using the STS temporary credentials and then fetches an API token from Conjur.

        Returns:
            str: The authentication token if successful, otherwise an empty string.
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

    def _authenticate_api_key(self):
        """
        Authenticates with Conjur using an API key.

        Returns:
            str: The authentication token if successful, otherwise an empty string.
        """

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._url}/authn/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {"Accept-Encoding": "base64"}
        response = requests.post(conjur_authenticate_uri,
                                 data=self._api_key,
                                 headers=headers)
        if response.status_code == 200:
            self._access_token = response.text

    def _get_conjur_headers(self) -> dict:
        if not self._access_token:
            self.connect()
        headers = {
            'Authorization': f'Token token="{self._access_token}"',
            'Content-Type': 'text/plain'
        }

        return headers

    @staticmethod
    def _get_branch_and_name_from_id(secret_id: str) -> Tuple[str, str]:
        """
        Gets a secret ID and splits the branch and secret name from it.

        :param secret_id: The input secret ID that may contain slashes.
        :return: The branch in which the secret is located, and the secret name.
        """

        # Check for an invalid input
        if not secret_id or "/" not in secret_id or "\n" in secret_id:
            return "", ""
        branch, secret_name = secret_id.rsplit("/", 1)
        return branch, secret_name

    def connect(self):
        if not self._authenticator_id:
            self._authenticate_api_key()
        elif self._authenticator_id.startswith("authn-iam"):
            self._authenticate_aws()

    def store(self, key: str, secret: str) -> None:
        branch, secret_name = self._get_branch_and_name_from_id(key)
        if not branch or not secret_name:
            return None

        url = f"{self._url}/policies/{self._account}/policy/{urllib.parse.quote(branch)}"
        policy_body = f"""
        - !variable
          id: {secret_name}
        """
        try:
            response = requests.post(url,
                                     data=policy_body,
                                     headers=self._get_conjur_headers())
            if response.status_code != 201:
                self.logger.error(f"Error creating secret: {response.text}")
                return None

            self.logger.info(response.text)

            set_secret_url = f"{self._url}/secrets/conjur/variable/{urllib.parse.quote(key)}"
            response = requests.post(set_secret_url,
                                     data=secret,
                                     headers=self._get_conjur_headers())
            if response.status_code != 200:
                self.logger.error(f"Error storing secret: {response.text}")
                return None

            self.logger.info(response.text)

        except Exception as e:
            self.logger.error(f"Error storing secret: {e}")

    def get(self, key: str) -> Optional[str]:
        if not self._access_token:
            self.connect()
        url = f"{self._url}/secrets/{self._account}/variable/{urllib.parse.quote(key)}"

        try:
            response = requests.get(url, headers=self._get_conjur_headers())
            if response.status_code != 200:
                self.logger.error(f"Error retrieving secret: {response.text}")
                return None
            return response.text
        except Exception as e:
            self.logger.error(f"Error retrieving secret: {e}")
            return None

    def delete(self, key: str) -> None:
        branch, secret_name = self._get_branch_and_name_from_id(key)
        if not branch or not secret_name:
            return None

        url = f"{self._url}/policies/{self._account}/policy/{urllib.parse.quote(branch)}"
        policy_body = f"""
        - !delete
          record: !variable {secret_name}
        """
        try:
            response = requests.patch(url,
                                      data=policy_body,
                                      headers=self._get_conjur_headers())
            if response.status_code != 200:
                self.logger.error(f"Error deleting secret: {response.text}")
                return None

            self.logger.info(response.text)
        except Exception as e:
            self.logger.error(f"Error deleting secret: {e}")
