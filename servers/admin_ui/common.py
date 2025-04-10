# Define an Enum for secret provider options
import os
from enum import Enum
from pathlib import Path

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
SECRET_NAMESPACE_KEY = "SECRET_NAMESPACE"
CONFIG_NAMESPACE = '../server.env'


class SecretProviderOptions(Enum):
    AWS_SECRETS_MANAGER_PROVIDER = "AWS Secrets Manager"
    FILE_SECRET_PROVIDER = "local.env file"
    CONJUR_SECRET_PROVIDER = "CyberArk Conjur Cloud"


secret_provider_name = None
secret_provider_namespace = None


def get_secret_provider():
    global secret_provider_name, secret_provider_namespace

    config_provider = FileSecretsProvider(namespace=CONFIG_NAMESPACE)
    configuration = config_provider.get_secret_dictionary()
    secret_provider_id = configuration.get(SECRET_PROVIDER_KEY)
    namespace = configuration.get(SECRET_NAMESPACE_KEY)
    secret_provider_namespace = namespace if namespace else ""

    provider_mapping = {
        SecretProviderOptions.FILE_SECRET_PROVIDER.name:
        (FileSecretsProvider,
         SecretProviderOptions.FILE_SECRET_PROVIDER.value),
        SecretProviderOptions.AWS_SECRETS_MANAGER_PROVIDER.name:
        (AWSSecretsProvider,
         SecretProviderOptions.AWS_SECRETS_MANAGER_PROVIDER.value),
        SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
        (ConjurSecretsProvider,
         SecretProviderOptions.CONJUR_SECRET_PROVIDER.value),
    }

    provider_info = provider_mapping.get(secret_provider_id)
    if not provider_info:
        raise Exception("Secret provider undefined")

    provider_class, provider_name = provider_info

    with EnvironmentVariablesManager(config_provider):
        secret_provider = provider_class(namespace=secret_provider_namespace)

    secret_provider_name = provider_name
    return secret_provider


def get_secret_provider_name() -> str:
    global secret_provider_name
    if not secret_provider_name:
        get_secret_provider()
    return secret_provider_name


def get_secret_provider_namespace() -> str:
    global secret_provider_namespace
    if secret_provider_namespace is None:
        get_secret_provider()
    return secret_provider_namespace


def print_header(title: str, sub_title: str):
    col0, col1, col2 = st.columns([2, 1, 6],
                                  gap='small',
                                  vertical_alignment='top',
                                  border=False)
    with col0:
        # Check if the logo file exists
        logo_path = os.path.join(str(Path(__file__).parent.parent.parent),
                                 "resources", "logo.png")
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
        st.header(title)
        st.subheader(sub_title)
