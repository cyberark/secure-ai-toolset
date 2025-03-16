import json
# this is an implementation of the secrets provider interface for CyberArk Conjur
from pydantic import SecretStr

import os

import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


class ConjurSecretsProvider(BaseSecretsProvider):
    def __init__(self):
        super().__init__()

        self._conjur_url = os.getenv('CONJUR_APPLIANCE_URL')
        self._workload_id = os.getenv('CONJUR_AUTHN_LOGIN')
        self._api_key = os.getenv('CONJUR_AUTHN_API_KEY')
        self._authenticator_id = os.getenv('CONJUR_AUTHENTICATOR_ID')
        self._account = os.getenv('CONJUR_ACCOUNT', 'conjur')
        self._region = os.getenv('CONJUR_AUTHN_IAM_REGION', 'us-east-1')
        self._conjur_token = None
        # ...initialize Conjur client...

        self.conjur_url = os.getenv('CONJUR_URL')
        self.workload_id = os.getenv('WORKLOAD_ID')
        self.region = os.getenv('CONJUR_REGION')
        self.conjur_token = None

    def _authenticate_aws(self):
        """
        Authenticates with Conjur using AWS IAM role.

        This function uses AWS IAM credentials to authenticate with Conjur. It signs a request using the STS temporary credentials and then fetches an API token from Conjur.
    def get_conjur_token_using_aws_sts(self, signed_headers) -> str:
       # Fetch an API token from Conjur
        conjur_authenticate_uri = f'{self.conjur_url}/authn-iam/aws/conjur/{self.workload_id.replace("/", "%2F")}/authenticate'
        headers = {'Accept-Encoding': 'base64'}
        response = requests.post(conjur_authenticate_uri,
                                data=signed_headers,
                                headers=headers)
        if not response or response.status_code != 200:
            raise Exception("Conjur not authenticated")

        return response.text

        Returns:
            str: The authentication token if successful, otherwise an empty string.
        """

        session = boto3.Session()
        credentials = session.get_credentials()
        credentials = credentials.get_frozen_credentials()

        # Sign the request using the STS temporary credentials
        sigv4 = SigV4Auth(credentials, 'sts', self._region)
        sts_uri = f'https://sts.{self._region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'
        request = AWSRequest(method='GET', url=sts_uri)
        sigv4.add_auth(request)
        signed_headers = json.dumps(dict(request.headers))

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._conjur_url}/{self._authenticator_id}/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {'Accept-Encoding': 'base64'}
        response = requests.post(conjur_authenticate_uri,
                                 data=signed_headers,
                                 headers=headers)
        if response.status_code == 200:
            self._conjur_token = response.text

    def _authenticate_api_key(self):
        """
        Authenticates with Conjur using an API key.

        Returns:
            str: The authentication token if successful, otherwise an empty string.
        """

        # Fetch an access token from Conjur
        conjur_authenticate_uri = f'{self._conjur_url}/authn/{self._account}/{self._workload_id.replace("/", "%2F")}/authenticate'
        headers = {'Accept-Encoding': 'base64'}
        response = requests.post(conjur_authenticate_uri,
                                 data=self._api_key,
                                 headers=headers)
        if response.status_code == 200:
            self._conjur_token = response.text

    def connect(self):
        if self._authenticator_id.startswith('authn-iam'):
            self._authenticate_aws()
        else:
            self._authenticate_api_key()

    def _get_conjur_headers(self) -> dict:
        if not self._conjur_token:
            self.connect()
        token = self._conjur_token
        headers = {
            'Authorization': f'Token token="{token}"',
            'Content-Type': 'text/plain'
        }

        return headers

    def store(self, key: str, secret: str) -> None:
        # ...store secret logic...
        url = f"{self._conjur_url}/policies/conjur/policy/data/gils"
        parts = key.split("/")
        policy_key = parts[0]
        policy_body = f"""
            - !variable
              id: secret12
              owner: !host new-host
        """
        try:
            response = requests.post(url,
                                     data=policy_body,
                                     headers=self._get_conjur_headers())
            if response.status_code != 201:
                return ''

            create_output = json.loads(response.text)
            self.logger.info(create_output)

            # store value of variable
            kind = "variable"
            identifier = f'conjur:host:data/hr-agent-poc/gil-test_policy/new-host/{key}'
            set_secret_url = f"{self._conjur_url}/secrets/conjur/{kind}/{identifier}"
            response = requests.post(set_secret_url,
                                     data=secret,
                                     headers=self._get_conjur_headers())


        except Exception as e:
            self.logger.error(e)

    def get(self, key: str) -> str:
        if not self._conjur_token:
            self.connect()
        url = f'{self._conjur_url}/secrets/conjur/variable/{key}'

        response = requests.get(url, headers=self._get_conjur_headers())
        if response.status_code != 200:
            return ''
        return response.text

    def delete(self, key: str) -> str:
        # ...delete secret logic...
        pass
