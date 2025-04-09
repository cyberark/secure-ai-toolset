from typing import Dict, Optional

from pydantic import BaseModel, model_validator

from servers.admin_ui.common import (CONJUR_APPLIANCE_URL_KEY, CONJUR_AUTHN_API_KEY_KEY, CONJUR_AUTHN_LOGIN_KEY,
                                     SECRET_NAMESPACE_KEY, SECRET_PROVIDER_KEY)


class ServerConfig(BaseModel):
    SECRET_PROVIDER: Optional[str] = None
    SECRET_NAMESPACE: Optional[str] = None
    CONJUR_AUTHN_LOGIN: Optional[str] = None
    CONJUR_AUTHN_API_KEY: Optional[str] = None
    CONJUR_APPLIANCE_URL: Optional[str] = None

    @model_validator(mode="after")
    def validate_fields(self):
        if self.SECRET_PROVIDER == "CONJUR_SECRET_PROVIDER":  # Fixed attribute reference
            missing_fields = []
            if not self.CONJUR_AUTHN_LOGIN:
                missing_fields.append("CONJUR_AUTHN_LOGIN")
            if not self.CONJUR_AUTHN_API_KEY:
                missing_fields.append("CONJUR_AUTHN_API_KEY")
            if not self.CONJUR_APPLIANCE_URL:
                missing_fields.append("CONJUR_APPLIANCE_URL")

            if missing_fields:
                raise ValueError(
                    f"Missing fields required for CONJUR_SECRET_PROVIDER: {', '.join(missing_fields)}"
                )

        # # Add validation for FILE_SECRET_PROVIDER
        # if self.SECRET_PROVIDER == "FILE_SECRET_PROVIDER" and self.SECRET_NAMESPACE:
        #     if "/" in self.SECRET_NAMESPACE or "\\" in self.SECRET_NAMESPACE:
        #         raise ValueError(
        #             "SECRET_NAMESPACE cannot contain '/' or '\\' when using FILE_SECRET_PROVIDER"
        #         )
        return self

    @staticmethod
    def load_from_dict(config: Dict):
        config = ServerConfig(
            SECRET_PROVIDER=config.get(SECRET_PROVIDER_KEY,
                                       "FILE_SECRET_PROVIDER"),
            SECRET_NAMESPACE=config.get(SECRET_NAMESPACE_KEY, "server"),
            CONJUR_APPLIANCE_URL=config.get(CONJUR_APPLIANCE_URL_KEY),
            CONJUR_AUTHN_LOGIN=config.get(CONJUR_AUTHN_LOGIN_KEY),
            CONJUR_AUTHN_API_KEY=config.get(CONJUR_AUTHN_API_KEY_KEY))
        return config
