import logging

import click

from agent_guard_core.api.identity.handler import IdentityConfig, IdentityHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group(name="idp")
def idp_login():
    """Commands to manage Identity Provider (IDP) operations in Agent Guard."""

@idp_login.command(name="login", help="Login to the Identity Provider (IDP) and obtain tokens.")
@click.option(
    '--domain',
    help='The IDP domain (e.g., "company.id.cyberark.cloud")',
    required=True
)
@click.option(
    '--client-id',
    help='The client ID for the application',
    required=True
)
@click.option(
    '--app-id',
    help='The application ID in the IDP',
    required=True
)
def login(domain: str, client_id: str, app_id: str):
    """Login to the IDP and obtain access tokens."""
    config = get_config(domain, client_id, app_id)
    logger.debug("Logging in to IDP with config: %s", config)

    oidc = IdentityHandler(config)
    oidc.login()
    
    if oidc.access_token is None:
        raise RuntimeError("Login failed. No access token received.")
    
    logger.info("Login successful.")

@idp_login.command(name="logout", help="Logout and clear all stored tokens.")
def logout():
    """Logout and remove all stored tokens."""
    logger.debug("Logging out from IDP")

    oidc = IdentityHandler()
    oidc.logout()
    
    logger.info("Logout successful. All tokens have been cleared.")
    
def get_config(domain: str, client_id: str, app_id: str) -> IdentityConfig:
    """Get the IDP configuration."""
    return IdentityConfig( 
        domain=domain,
        client_id=client_id,
        app_id=app_id
    )