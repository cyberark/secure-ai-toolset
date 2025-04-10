import os
from pathlib import Path

import streamlit as st

from servers.admin_ui.common import print_header

# Set the working directory to the file's directory
current_dir = Path(__file__).resolve().parent
os.chdir(current_dir)

# configure streamlit
st.set_page_config(page_title="Agent Guard Management UI",
                   page_icon="🛡️",
                   layout="wide")

print_header(title="Agent Guard", sub_title="Securing Agentic AI")

st.write("\n\n")
st.subheader("Welcome to Agent Guard!")
st.write("""
Agent Guard is your AI-driven security solution, offering the following capabilities:
- **Secret Provider**: Acts as a proxy to the following secret providers:
    - AWS Secrets Manager
    - CyberArk Conjur secret provider
    - Local file secret provider (for testing purposes and non sensitive data only) 
- **Environment keys editor**: A user-friendly interface for managing environment keys. 
    - The keys are stored in the selected secret provider.
- **REST API Server**: A set of REST APIs exposing the Agent Guard features. 
    - The server abstracts multiple providers in a single endpoint. 
    - It uses the provider selected in the configuration phase.
    - For more details, visit the [API server documentation](http://localhost:8081/docs).
""")
