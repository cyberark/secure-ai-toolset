from typing import List, Optional

from pydantic import BaseModel, Field, RootModel, model_validator

from agent_guard_core.credentials.enum import CredentialsProvider

SECRETS_URI_FORMAT = "{provider}://{key}/{env_var}"


class SecretUri(BaseModel):
    provider: CredentialsProvider = Field(..., description="The secret provider type")
    key: str = Field(..., description="The key to fetch the secret from the provider")
    env_var: Optional[str] = Field(None, description="The environment variable to set with the secret value")

    @model_validator(mode="after")
    def set_default_env_var(self):
        if not self.env_var:
            self.env_var = self.key
        return self

    @classmethod
    def from_uri(cls, uri: str) -> "SecretUri":
        """
        Parses a string like:
        - 'conjur://mysecret/MY_ENV_VAR'
        - 'conjur://mysecret'
        """
        try:
            scheme, rest = uri.split("://", 1)
            if "/" in rest:
                key, env_var = rest.split("/", 1)
                return cls(provider=scheme, key=key, env_var=env_var)
            else:
                return cls(provider=scheme, key=rest)
        except ValueError:
            raise ValueError(f"Invalid secret mapping URI: '{uri}'. " "Expected format '<provider>://<key>[/<env_var>]'")

    @classmethod
    def from_env_var(cls, env_var_key: str, env_var_value: str) -> "SecretUri":
        """
        Joins an environment variable key and value into a SecretUri.
        Example: 'key: MY_ENV_VAR, value: conjur://mysecret' -> SecretUri(provider='conjur', key='mysecret', env_var='MY_ENV_VAR')
        """
        if "://" not in env_var_value:
            raise ValueError(f"Invalid secret mapping value: '{env_var_value}'. Expected format '<provider>://<key>'")
        provider, secret_key = env_var_value.split("://", 1)
        return cls.from_uri(SECRETS_URI_FORMAT.format(provider=provider, key=secret_key, env_var=env_var_key))


class SecretUriList(RootModel):
    """
    A list of SecretUri objects.
    This is used to parse a list of secret URIs from the command line.
    """

    root: List[SecretUri] = Field(default_factory=list, description="List of secret URIs")

    @classmethod
    def from_uris(cls, uris: list[str]) -> "SecretUriList":
        secret_uris = []
        for uri in uris:
            try:
                secret_uris.append(SecretUri.from_uri(uri))
            except ValueError as e:
                # You had an ellipsis here - decide what you want to do with errors
                # Either raise or log them, but don't silently ignore
                pass
        return cls(root=secret_uris)

    @classmethod
    def from_env_vars(cls, env_vars: list[tuple[str, str]]) -> "SecretUriList":
        secret_uris = []
        for env_var_key, value in env_vars:
            # try to parse the environment variable key and value into a SecretUri
            try:
                secret_uris.append(SecretUri.from_env_var(env_var_key=env_var_key, env_var_value=value))
            except ValueError as e:
                continue
        return cls(root=secret_uris)
