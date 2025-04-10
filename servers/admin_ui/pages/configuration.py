import os
# Replace the text input with a file picker if the selected provider is FileSecretsProvider
from pathlib import Path

import streamlit as st

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from servers.admin_ui.common import (CONFIG_NAMESPACE, CONJUR_APPLIANCE_URL_KEY, CONJUR_AUTHN_API_KEY_KEY,
                                     CONJUR_AUTHN_LOGIN_KEY, SECRET_NAMESPACE_KEY, SECRET_PROVIDER_KEY,
                                     SecretProviderOptions, print_header)
from servers.admin_ui.models.server_config import ServerConfig


def file_selector(folder_path='.'):
    # List only directories not starting with '.'
    entries = os.listdir(folder_path)
    directories = [
        entry for entry in entries
        if os.path.isdir(os.path.join(folder_path, entry))
        and not entry.startswith('.')
    ]
    selected_directory = st.selectbox('Select a directory (From users home)', directories)
    return os.path.join(folder_path, selected_directory)


def save_configuration(provider: FileSecretsProvider, config: ServerConfig):

    provider.store(SECRET_PROVIDER_KEY, config.SECRET_PROVIDER)
    provider.store(SECRET_NAMESPACE_KEY, config.SECRET_NAMESPACE)

    # Save Conjur-specific configuration if applicable
    if 'CONJUR_SECRET_PROVIDER' in config.SECRET_PROVIDER:
        provider.store(CONJUR_AUTHN_LOGIN_KEY, config.CONJUR_AUTHN_LOGIN)
        provider.store(CONJUR_AUTHN_API_KEY_KEY, config.CONJUR_AUTHN_API_KEY)
        provider.store(CONJUR_APPLIANCE_URL_KEY, config.CONJUR_APPLIANCE_URL)


try:
    config_provider = FileSecretsProvider(namespace=CONFIG_NAMESPACE)
except Exception as e:
    st.error(f"Failed to initialize FileSecretsProvider: {e}")
    st.stop()

# Display the title and subtitle of the page
print_header(title="Configuration", sub_title="Manage Agent Guard settings")

# Load configuration from server_config
configuration_dict = config_provider.get_secret_dictionary()
config: ServerConfig = ServerConfig.load_from_dict(configuration_dict)
if not configuration_dict:
    st.warning(
        "Configuration file is missing or empty. Generating default settings")
    save_configuration(provider=config_provider, config=config)

# Retrieve the currently configured secret provider
# configured_secret_provider = config.SECRET_PROVIDER
configured_secret_provider_value = SecretProviderOptions[
    config.SECRET_PROVIDER].value


# Callback function to handle changes in the secret provider selectbox
# This sets a flag in the session state to trigger a rerun
def on_secret_provider_change():
    st.session_state.trigger_rerun = True


# Select the secret provider using a dropdown (selectbox)
secret_provider_value = st.selectbox(
    "**Secret Provider**",  # Label for the selectbox
    [option.value
     for option in SecretProviderOptions],  # Options for the dropdown
    index=[option.value for option in SecretProviderOptions
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
    for key, option in SecretProviderOptions.__members__.items()
}.get(secret_provider_value)
config.SECRET_PROVIDER = selected_secret_provider_key


users_home = Path.home()
if selected_secret_provider_key == SecretProviderOptions.FILE_SECRET_PROVIDER.name:
    dir = file_selector(folder_path=users_home)
    file_name = st.text_input("File Name")
    namespace = os.path.join(dir, file_name)
    st.write(f"File location: {namespace}")
else:
    namespace = st.text_input(SECRET_NAMESPACE_KEY, config.SECRET_NAMESPACE)

config.SECRET_NAMESPACE = namespace
# Display provider-specific inputs
if selected_secret_provider_key == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
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
        if selected_secret_provider_key == SecretProviderOptions.FILE_SECRET_PROVIDER.name and not file_name.strip():
            st.error("File Name is required!")
        else:
            save_configuration(provider=config_provider, config=config)
            st.success("Configuration saved successfully!")
