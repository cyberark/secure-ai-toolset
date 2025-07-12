# Replace the text input with a file picker if the selected provider is FileSecretsProvider

import streamlit as st

from agent_guard_core.credentials.enum import CredentialsProvider
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from servers.admin_ui.models.server_config import ServerConfig
from servers.common import (CONJUR_APPLIANCE_URL_KEY, CONJUR_AUTHN_API_KEY_KEY, CONJUR_AUTHN_LOGIN_KEY,
                            SECRET_NAMESPACE_KEY, SECRET_PROVIDER_KEY, get_config_file_path, print_header)


def save_configuration(provider: FileSecretsProvider, config: ServerConfig):

    provider.store(SECRET_PROVIDER_KEY, config.SECRET_PROVIDER)
    provider.store(SECRET_NAMESPACE_KEY, config.SECRET_NAMESPACE)

    # Save Conjur-specific configuration if applicable
    if 'CONJUR_SECRET_PROVIDER' == config.SECRET_PROVIDER:
        provider.store(CONJUR_AUTHN_LOGIN_KEY, config.CONJUR_AUTHN_LOGIN)
        provider.store(CONJUR_AUTHN_API_KEY_KEY, config.CONJUR_AUTHN_API_KEY)
        provider.store(CONJUR_APPLIANCE_URL_KEY, config.CONJUR_APPLIANCE_URL)


## Configuration form beginning
print_header(title="Configuration", sub_title="Manage Secret Store Settings")

# Read configuration file
try:
    config_file_path = get_config_file_path()
    config_provider = FileSecretsProvider(namespace=config_file_path)
    configuration_dict = config_provider.get()
    if not configuration_dict:
        st.warning(
            "Configuration file is missing or empty. Generating default settings"
        )
        configuration_dict = {}
    config: ServerConfig = ServerConfig.load_from_dict(configuration_dict)
    save_configuration(provider=config_provider, config=config)
except Exception as e:
    st.error(f"Failed to initialize FileSecretsProvider: {e}")
    st.stop()

# Load configuration from server_config
configured_secret_provider_value = config.SECRET_PROVIDER


# Callback function to handle changes in the secret provider select box
# This sets a flag in the session state to trigger a rerun
def on_secret_provider_change():
    st.session_state.trigger_rerun = True


# Select the secret provider using a dropdown (selectbox)
secret_provider_value = st.selectbox(
    "**Secret Provider**",  # Label for the selectbox
    [option.value
     for option in CredentialsProvider],  # Options for the dropdown
    index=[option.value for option in CredentialsProvider
           ].index(configured_secret_provider_value
                   ),  # Pre-select the currently configured provider
    on_change=on_secret_provider_change)

# Check if a rerun is triggered and reset the flag to avoid infinite loops
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.rerun()

# Map the selected provider value to its corresponding key
selected_secret_provider_key = {
    option.value: key
    for key, option in CredentialsProvider.__members__.items()
}.get(secret_provider_value)
config.SECRET_PROVIDER = selected_secret_provider_key

# Get the namespace
label = "**File Path(Namespace)**" if selected_secret_provider_key == CredentialsProvider.FILE_DOTENV else "**Namespace**"
config.SECRET_NAMESPACE = st.text_input(label, config.SECRET_NAMESPACE)

# Display provider-specific inputs
if selected_secret_provider_key == CredentialsProvider.CONJUR:
    # Retrieve existing Conjur configuration values
    conjur_authn_login = config.CONJUR_AUTHN_LOGIN
    conjur_authn_api_key = config.CONJUR_AUTHN_API_KEY
    conjur_appliance_url = config.CONJUR_APPLIANCE_URL

    # Input fields for Conjur-specific configuration
    conjur_authn_login = st.text_input(CONJUR_AUTHN_LOGIN_KEY,
                                       conjur_authn_login)
    conjur_authn_api_key = st.text_input(CONJUR_AUTHN_API_KEY_KEY,
                                         conjur_authn_api_key,
                                         type="password")
    conjur_appliance_url = st.text_input(CONJUR_APPLIANCE_URL_KEY,
                                         conjur_appliance_url)
# Wrap the form logic
with st.form("configuration_form"):
    # Submit button to save the configuration
    submitted = st.form_submit_button("Save Configuration")
    if submitted:
        save_configuration(provider=config_provider, config=config)
        st.success("Configuration saved successfully!")
