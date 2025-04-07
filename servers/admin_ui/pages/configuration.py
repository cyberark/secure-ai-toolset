import os  # Added import for os

import streamlit as st

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from servers.admin_ui.common import SecretProviderOptions, print_header

# Update configuration file location to the parent directory of this file
config_file_dir = os.path.join(os.path.dirname(__file__), os.pardir)
server_config_provider = FileSecretsProvider(directory=config_file_dir)

# Define constants for configuration keys
CONJUR_AUTHN_LOGIN_KEY = "CONJUR_AUTHN_LOGIN"
CONJUR_AUTHN_API_KEY_KEY = "CONJUR_AUTHN_API_KEY"
CONJUR_APPLIANCE_URL_KEY = "CONJUR_APPLIANCE_URL"
SECRET_PROVIDER_KEY = "SECRET_PROVIDER"

# Load configuration from server_config
configuration = server_config_provider.get_secret_dictionary()

# Display the title and subtitle of the page
st.set_page_config(layout="wide")
print_header(title="Configuration", sub_title="Manage Agent Guard settings")

# Retrieve the currently configured secret provider
configured_secret_provider = configuration.get(SECRET_PROVIDER_KEY)
configured_secret_provider_value = SecretProviderOptions[
    configured_secret_provider].value


# Callback function to handle changes in the secret provider selectbox
# This sets a flag in the session state to trigger a rerun
def on_secret_provider_change():
    if selected_secret_provider_key == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
        st.session_state.trigger_rerun = True


# Select the secret provider using a dropdown (selectbox)
secret_provider_value = st.selectbox(
    "**Secret Provider**",  # Label for the selectbox
    [option.value
     for option in SecretProviderOptions],  # Options for the dropdown
    index=[option.value for option in SecretProviderOptions
           ].index(configured_secret_provider_value
                   ),  # Pre-select the currently configured provider
    on_change=on_secret_provider_change  # Callback to handle changes
)

# Check if a rerun is triggered and reset the flag to avoid infinite loops
if st.session_state.get("trigger_rerun"):
    st.session_state.trigger_rerun = False
    st.rerun()

# Map the selected provider value to its corresponding key
selected_secret_provider_key = {
    option.value: key
    for key, option in SecretProviderOptions.__members__.items()
}.get(secret_provider_value)

# Display Conjur-specific inputs only if the selected provider is Conjur
if selected_secret_provider_key == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
    # Retrieve existing Conjur configuration values
    conjur_authn_login = configuration.get(CONJUR_AUTHN_LOGIN_KEY)
    conjur_authn_api_key = configuration.get(CONJUR_AUTHN_API_KEY_KEY)
    conjur_appliance_url = configuration.get(CONJUR_APPLIANCE_URL_KEY)

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
        # Save the selected secret provider key
        server_config_provider.store(SECRET_PROVIDER_KEY,
                                     selected_secret_provider_key)
        # Display a success message
        st.success("Configuration saved successfully!")
