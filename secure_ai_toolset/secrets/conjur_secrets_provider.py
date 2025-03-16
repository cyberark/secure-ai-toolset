# this is an implementation of the secrets provider interface for CyberArk Conjur
from pydantic import SecretStr

from secure_ai_toolset.secrets.secrets_provider import BaseSecretsProvider


class ConjurSecretsProvider(BaseSecretsProvider):

    def __init__(self):
        super().__init__()
        # ...initialize Conjur client...
        pass

    def connect(self):
        pass

    def store(self, key: str, secret: str) -> None:
        # ...store secret logic...
        pass

    def get(self, key: str) -> SecretStr:
        # ...retrieve secret logic...
        pass

    def delete(self, key: str) -> str:
        # ...delete secret logic...
        pass
