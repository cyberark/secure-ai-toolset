from pathlib import Path

import streamlit as st


# Function to read the .env file
def read_env_file(env_path):
    if env_path.exists():
        with env_path.open() as f:
            return f.read()
    return ""


# Function to write to the .env file
def write_env_file(env_path, content):
    with env_path.open("w") as f:
        f.write(content)


# Path to the .env file
env_path = Path(".env")

st.title("Configure .env File")

# Combo box for selecting the secret provider
secret_provider = st.selectbox("Select Secret Provider",
                               ["Local .env file", "AWS Secret Manager"])

if secret_provider == "Local .env file":
    # Read the current content of the .env file
    env_content = read_env_file(env_path)

    # Text area for editing the .env file
    new_env_content = st.text_area("Edit .env file", env_content, height=300)

    # Save button
    if st.button("Save"):
        write_env_file(env_path, new_env_content)
        st.success("Saved successfully!")
elif secret_provider == "AWS Secret Manager":
    st.write("AWS Secret Manager configuration is not implemented yet.")
