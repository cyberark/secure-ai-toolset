# this is an implementation of the secrets provider interface for CyberArk Conjur
from pydantic import SecretStr

import json
import boto3
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider
import os
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import requests

class ConjurSecretsProvider(BaseSecretsProvider):

    def __init__(self):
        super().__init__()
        # ...initialize Conjur client...

        self.conjur_url = os.getenv('CONJUR_URL')
        self.workload_id = os.getenv('WORKLOAD_ID')
        self.conjur_token = None

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

    def connect(self):
        pass

        session = boto3.Session()
        credentials = session.get_credentials()
        frozen_credentials = credentials.get_frozen_credentials()

        # Sign the request using the STS temporary credentials
        sigv4 = SigV4Auth(credentials, 'sts', region)
        sts_uri = f'https://sts.{region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'
        request = AWSRequest(method='GET', url=sts_uri)
        sigv4.add_auth(request)
        signed_headers = json.dumps(dict(request.headers))

        self.conjur_token = self.get_conjur_token_using_aws_sts()



    def store(self, key: str, secret: str) -> None:
        # ...store secret logic...
        pass

    def get(self, key: str) -> str:
        # ...retrieve secret logic...
        pass
    def get(self, key: str) -> str:

        headers = {
            'Authorization': f'Token token="{self.conjur_token}"',
        }
        url = f'{self.conjur_url}/secrets/conjur/variable/{key}'
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return ''
        return response.text


    def delete(self, key: str) -> str:
        # ...delete secret logic...
        pass
