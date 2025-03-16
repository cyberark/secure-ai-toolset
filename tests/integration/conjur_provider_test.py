from typing import List
import pytest
from secure_ai_toolset.secrets.aws_secrets_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.conjur_secrets_provider import ConjurSecretsProvider
from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


def test_provider_ctor():
    provider = ConjurSecretsProvider()
    assert provider is not None


def test_create_get_delete_secret():
    provider = ConjurSecretsProvider()
    
    key = "data/test-toolset/my-environment"
    secret = "test"
    provider.store(key=key, secret=secret)

    fetched_secret = provider.get(key=key)
    assert fetched_secret == secret

    provider.delete(key=key)
    assert provider.get(key=key) == ""
