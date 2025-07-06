import pandas as pd
import streamlit as st

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.secrets_provider import SecretProviderException
from servers.common import get_secret_provider, get_secret_provider_name, get_secret_provider_namespace, print_header


def save_edits(edited_secrets: pd.DataFrame):
    try:
        # iterate over edited secrets rows
        updated_secrets = {}
        for row in edited_secrets.iterrows():
            key, value = row[1]
            if key and key not in updated_secrets:
                updated_secrets[key] = value
            elif key in updated_secrets:
                st.warning(f"Duplicate key found:{key}")

        # Save the updated secrets back to the secret provider
        if len(updated_secrets) > 0:
            secret_provider.store(updated_secrets)
            st.success("Secrets updated successfully!")
        else:
            st.warning("Trying to save an empty list")
    except SecretProviderException as e:
        st.error(f"Failed to save secrets: {e.args[0]}")
    except Exception as e:
        st.error(
            f"An unexpected error occurred while saving secrets: {str(e)}")


# get server configuration
secrets_dictionary = None
try:
    secret_provider = get_secret_provider()
    secret_provider_name = get_secret_provider_name()
    secret_provider_namespace = get_secret_provider_namespace()
    print_header(
        title="Environment Variables Editor",
        sub_title=
        f"Secret Provider: {secret_provider_name} (Namespace: {secret_provider_namespace})"
    )

    secrets_dictionary = secret_provider.get()

except SecretProviderException as e:
    if "ExpiredTokenException" in e.args[0] and isinstance(
            secret_provider, AWSSecretsProvider):
        st.error(
            "Your AWS Token is expired. Please update your AWS credentials.")
    else:
        st.error(f"An exception occurred: {e.args[0]}")
except Exception as e:
    st.error(f"An unexpected error occurred: {str(e)}")

# Display the secrets dictionary in a Streamlit data editor
if secrets_dictionary is None:
    st.warning("No secrets found in the selected secret provider.")
else:
    env_vars_dataframe = pd.DataFrame(list(secrets_dictionary.items()),
                                      columns=["Key", "Value"])
    edited_secrets = st.data_editor(
        env_vars_dataframe,
        column_config={
            "Key":
            st.column_config.Column(
                "Environment Variable Key",
                help="The environment variable key",
                width="medium",
                required=True,
            ),
            "Value":
            st.column_config.TextColumn(
                "Environment Variable Value",
                help=
                "The environment variable value, can be an API key, path definitions etx",
                width="medium",
                required=True,
            )
        },
        num_rows="dynamic")

    if st.button("Save Changes"):
        save_edits(edited_secrets)
