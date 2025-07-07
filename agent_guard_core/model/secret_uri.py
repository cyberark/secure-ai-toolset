from typing import Optional

from pydantic import BaseModel, Field, model_validator

from agent_guard_core.credentials.enum import CredentialsProvider


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
            raise ValueError(f"Invalid secret mapping URI: '{uri}'. "
                             "Expected format '<provider>://<key>[/<env_var>]'")

