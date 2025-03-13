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
        self.region = os.getenv('CONJUR_REGION')
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
        session = boto3.Session()
        credentials = session.get_credentials()
        frozen_credentials = credentials.get_frozen_credentials()
        # check if region is empty

        # Sign the request using the STS temporary credentials
        sigv4 = SigV4Auth(credentials, 'sts', self.region)
        sts_uri = f'https://sts.{self.region}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'
        request = AWSRequest(method='GET', url=sts_uri)
        sigv4.add_auth(request)
        signed_headers = json.dumps(dict(request.headers))

        self.conjur_token = self.get_conjur_token_using_aws_sts(signed_headers=signed_headers)

    def _get_conjur_headers(self) ->str:
        if not self.conjur_token:
            self.connect()
        # token = 'eyJwcm90ZWN0ZWQiOiJleUpoYkdjaU9pSmpiMjVxZFhJdWIzSm5MM05zYjNOcGJHOHZkaklpTENKcmFXUWlPaUprWmpkbVptUTNNVFF5WVRsaE5UVTJNemRpT0RsbE5EZG1NbVkyWlRFelpUSTJaR1UyTURsak9XSmtaalF3T0RWbVpEUm1OakE1TVRnNU1UVXhORE0ySW4wPSIsInBheWxvYWQiOiJleUpwWVhRaU9qRTNOREU0TmpJMU1UUXNJbk4xWWlJNkltZHBiRjloWkdSaFFHTjVZbVZ5WVhKckxtTnNiM1ZrTGpNeU1qSTRNeUlzSW1WNGNDSTZNVGMwTVRnMk5qRXhOQ3dpZEdsa0lqb2laREl4WTJaaE1qWXROREE0T0MwME4yUmlMVGxpWWpFdE5tWTRZelE1TkdGbU1EWmtJbjA9Iiwic2lnbmF0dXJlIjoiWWZmdFNONmY1eTUyZmhMSG95ZHV5SGhDd3N3TzVFUktqUXVyRmZIdnN1R3hoLWJPcW82TGtoZWpOZmczQWhFbG5BU3g3RUZuVGxRdExxUHhFdm5FVXBKMHotT1BObXprY3dZbWExUnAtTU1pQWFvc21VS1VVMnh6NXFTdzBhQUxiVEJkWS10NEh3RGR6RzlONTVsR3JLV2NLNkp2UWE1d1ZRcHpSRmE3emtpXzJoaWtRbFk0YmdMb3IydDhHbEU3aHRFU3hNTUxwOXh4b3ZQam8xa3hadmhVMjh3cGNKQWdCU2hJNHczWkNQLUNVUndFVTVFRm5yYnFsa20wOTJJTE4yaGtkNmFwN3NNXzBRb0N4MWt5NGQyckdJUUVOSGx3TWZrS3hBMVQ3Y3FMaXNfXzY5Nk8yX3VCTmdLeFBIZmJwUnBIQ1hoQzNUQjZDNDA5aXIxNjhPVUVwNTlwTGNPaUJpdl9VOWFmZ0FiY2MtNEJKZWJ0amZ2Zkh2OWxhZUo2In0='
        token = self.conjur_token
        headers = {
            'Authorization': f'Token token="{token}"',
            'Content-Type': 'text/plain'
        }

        return headers

    "/data/gils/subfolder/secret12"
    def store(self, key: str, secret: str) -> None:
        # ...store secret logic...
        url = f"{self.conjur_url}/policies/conjur/policy/data/gils"
        parts = key.split("/")
        host = "authn-iam/aws/450676674096/AWSReservedSSO_NeoDeveloper_c1b66fa92e7669fe"
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
            set_secret_url = f"{self.conjur_url}/secrets/conjur/{kind}/{identifier}"
            response = requests.post(set_secret_url,
                                    data=secret,
                                    headers=self._get_conjur_headers())


        except Exception as e:
            self.logger.error(e)

    def get(self, key: str) -> str:
        if not self.conjur_token:
            self.connect()
        url = f'{self.conjur_url}/secrets/conjur/variable/{key}'

        response = requests.get(url, headers=self._get_conjur_headers())
        if response.status_code != 200:
            return ''
        return response.text


    def delete(self, key: str) -> str:
        # ...delete secret logic...
        pass
