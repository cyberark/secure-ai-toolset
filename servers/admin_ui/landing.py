import os

import streamlit as st

# Center the title
st.markdown("<h1 style='text-align: center;'>Agent Guard</h1>",
            unsafe_allow_html=True)

# Check if the logo file exists
logo_path = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir,
                         "resources", "logo.png")
if os.path.exists(logo_path):
    st.image(logo_path,
             use_container_width=True)  # Display the logo if it exists
else:
    st.warning(
        "Logo file not found. Please ensure 'agent_guard_logo.png' is in the correct directory."
    )

st.subheader("Welcome to Agent Guard!")
st.write("""
Agent Guard is your AI-driven security solution, offering the following capabilities:
- **Local Secret Provider**: Acts as a proxy to other secret providers.
- **Prompt Guard Server**: Ensures secure and controlled interactions with AI models.
- **Proxy Server**: Facilitates secure access to other servers.
- **Authentication and Access Control Server**: Manages user authentication and access control.
""")
