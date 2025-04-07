import os

import streamlit as st

from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider

# Load environment variables from .env file
server_configuration_provider = FileSecretsProvider()

st.title("Configuration")
st.subheader("Welcome to the Configuration page!")
st.write("Manage your settings and preferences here.")


# Map environment variable to selectbox options
# Define an Enum for secret provider options
class SecretProviderOptions(Enum):
    AWS_SECRET_MANAGER = "AWS Secret Manager"
    FILE_SECRET_PROVIDER = "local.env file"
    CONJUR_SECRET_PROVIDER = "CyberArk Conjur Cloud"

# Use the Enum to populate the selectbox
secret_provider = st.selectbox(
    "Secret Provider",
    [option.value for option in SecretProviderOptions],
    index=[option.value for option in SecretProviderOptions].index(
        SecretProviderOptions.FILE_SECRET_PROVIDER.value
    )

# Save configuration button
st.write("Selected Secret Provider:", secret_provider)
if st.button("Save Configuration"):
    server_configuration_provider.set("SECRET_PROVIDER", secret_provider)
    st.success("Configuration saved to .env file")
