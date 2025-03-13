from typing import List
import pytest
from secure_ai_toolset.secrets.aws_secrets_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.conjur_secrets_provider import ConjurSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


def test_provider_ctor():
    provider = ConjurSecretsProvider()
    assert provider is not None

def test_get_secret():
    provider = ConjurSecretsProvider()
    # key = "data/hr-agent-poc/env-data"
    # key = "data/hr-agent-poc/hr-db-user-id"a
    key = "data/hr-agent-poc/hr-db-user-password"
    secret = provider.get(key=key)
    assert secret


def test_create_secret():
    provider = ConjurSecretsProvider()
    
    secret_id = "gil1/test_key"
    secret = "blah"
    policy = "gil1"
    host = "authn-iam/aws/450676674096/AWSReservedSSO_NeoDeveloper_c1b66fa92e7669fe"
    provider.store(key=secret_id, secret=secret)

    fetched_secret = provider.get(key=key)
    assert fetched_secret

