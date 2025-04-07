import streamlit as st

from servers.admin_ui.common import print_header

# configure streamlit
st.set_page_config(layout="wide")
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
- **RestAPI Server**: A rest api exposing the Agent Guard features. 
    - The server abstracts multiple providers in a single endpoint. 
    - It uses the provider selected in the configuration phase.
    - For more details, visit the [API server documentation](http://localhost:8081/docs).
""")
