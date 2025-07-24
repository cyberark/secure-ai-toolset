import logging
import sys

import click

from agent_guard_core.cli.login_idp import idp_login
from agent_guard_core.cli.mcp_proxy_cli import mcp_proxy
from agent_guard_core.cli.secrets_cli import secrets
from agent_guard_core.credentials.enum import CredentialsProvider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

provider_list = [provider.value for provider in CredentialsProvider]

@click.group(help=(
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options.")
    )
def cli():
    """Entry point for the Agent Guard CLI."""
    
cli.add_command(secrets)
cli.add_command(mcp_proxy)
cli.add_command(idp_login)

if __name__ == '__main__':
    try:
        cli(sys.argv[1:], standalone_mode=False)
    except KeyboardInterrupt:
        logger.debug("KeyboardInterrupt caught at top level, exiting gracefully.")
        print("\nExiting Agent Guard CLI.")
        sys.exit(0)