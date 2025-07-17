# Define an Enum for secret provider options
import os
from enum import Enum
from pathlib import Path

import streamlit as st

from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.gcp_secrets_manager_provider import GCPSecretsProvider
from agent_guard_core.credentials.secrets_provider import secrets_provider_fm

# Define globals for cache
secret_provider_name = None
secret_provider_namespace = None

# Define constants for configuration keys
CONJUR_AUTHN_LOGIN_KEY = "CONJUR_AUTHN_LOGIN"
CONJUR_AUTHN_API_KEY_KEY = "CONJUR_AUTHN_API_KEY"
CONJUR_APPLIANCE_URL_KEY = "CONJUR_APPLIANCE_URL"
SECRET_PROVIDER_KEY = "SECRET_PROVIDER"
SECRET_NAMESPACE_KEY = "SECRET_NAMESPACE"


def get_config_file_path():
    file_dir = Path(__file__).parent.parent
    file_path = os.path.join(file_dir, "server_config.env")
    return file_path


def get_config_provider():
    config_provider = FileSecretsProvider(namespace=get_config_file_path())
    return config_provider


def get_secret_provider():
    config_provider = get_config_provider()
    configuration = config_provider.get()

    secret_provider_id = configuration.get(SECRET_PROVIDER_KEY)
    namespace = configuration.get(SECRET_NAMESPACE_KEY)
    secret_provider_namespace = namespace if namespace else ""

    with EnvironmentVariablesManager(get_config_provider()):
        secret_provider = secrets_provider_fm.get(secret_provider_id)(namespace=secret_provider_namespace)

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
        logo_path = os.path.join(str(Path(__file__).parent.parent),
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
