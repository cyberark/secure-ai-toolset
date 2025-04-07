# Define an Enum for secret provider options
import os
from enum import Enum

import streamlit as st

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider

# Define constants for configuration keys
CONJUR_AUTHN_LOGIN_KEY = "CONJUR_AUTHN_LOGIN"
CONJUR_AUTHN_API_KEY_KEY = "CONJUR_AUTHN_API_KEY"
CONJUR_APPLIANCE_URL_KEY = "CONJUR_APPLIANCE_URL"
SECRET_PROVIDER_KEY = "SECRET_PROVIDER"


class SecretProviderOptions(Enum):
    AWS_SECRET_MANAGER = "AWS Secret Manager"
    FILE_SECRET_PROVIDER = "local.env file"
    CONJUR_SECRET_PROVIDER = "CyberArk Conjur Cloud"


secret_provider_name = None


def get_secret_provider():
    global secret_provider_name

    config_file_dir = os.path.join(os.path.dirname(__file__))
    config_provider = FileSecretsProvider(directory=config_file_dir)

    configuration = config_provider.get_secret_dictionary()
    secret_provider_id = configuration.get(SECRET_PROVIDER_KEY)

    if secret_provider_id == SecretProviderOptions.FILE_SECRET_PROVIDER.name:
        secret_provider = FileSecretsProvider(namespace="secrets",
                                              directory=config_file_dir)
        secret_provider_name = SecretProviderOptions.FILE_SECRET_PROVIDER.value
    elif secret_provider_id == SecretProviderOptions.AWS_SECRET_MANAGER.name:
        secret_provider = AWSSecretsProvider()
        secret_provider_name = SecretProviderOptions.AWS_SECRET_MANAGER.value
    elif secret_provider_id == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
        with EnvironmentVariablesManager(config_provider):
            secret_provider = ConjurSecretsProvider(namespace='data/test')
        secret_provider_name = SecretProviderOptions.CONJUR_SECRET_PROVIDER.value
    else:
        raise Exception("Secret provider undefined")

    return secret_provider


def get_secret_provider_name() -> str:
    global secret_provider_name
    if not secret_provider_name:
        get_secret_provider()
    return secret_provider_name


def print_header(title: str, sub_title: str):
    col0, col1, col2 = st.columns([2, 1, 6],
                                  gap='medium',
                                  vertical_alignment='top',
                                  border=False)
    with col0:
        # Check if the logo file exists
        logo_path = os.path.join(os.path.dirname(__file__), os.pardir,
                                 os.pardir, "resources", "logo.png")
        if os.path.exists(logo_path):
            st.image(
                logo_path,
                use_container_width=False)  # Display the logo if it exists
        else:
            st.warning(
                "Logo file not found. Please ensure 'agent_guard_logo.png' is in the correct directory."
            )
    with col1:
        pass
    with col2:
        st.title(title)
        st.header(sub_title)
