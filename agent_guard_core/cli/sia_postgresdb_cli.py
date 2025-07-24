import asyncio
import logging
from typing import Optional
from urllib.parse import quote_plus

import click

from agent_guard_core.api.identity.handler import IdentityConfig, IdentityHandler
from agent_guard_core.api.sia.handler import SecureInfraAccessHandler
from agent_guard_core.cli.mcp_proxy_cli import ProxyCapability, _stdio_mcp_proxy_async

logger = logging.getLogger(__name__)

@click.group(name="sia-postgresdb", help="Connect to PostgreSQL databases using SIA")
def sia_postgresdb():
    """Commands for managing Secure Infrastructure Access PostgreSQL connections."""
    pass

@sia_postgresdb.command(name="connect", help="Connect to a PostgreSQL database using SIA credentials")
@click.option(
    '--username',
    '-u',
    required=True,
    help="Username for database access (e.g., myuser@cyberark.cloud)"
)
@click.option(
    '--tenant-id',
    '-t',
    required=True,
    help="Tenant ID (e.g., acmeinc)"
)
@click.option(
    '--db-host',
    '-h',
    required=True,
    help="Database host FQDN"
)
@click.option(
    '--database',
    '-d',
    default='postgres',
    help="Database name (default: postgres)"
)
@click.option(
    '--debug',
    is_flag=True,
    help="Enable debug logging"
)
def connect(username: str, tenant_id: str, db_host: str, database: str, debug: bool = False):
    """Connect to a PostgreSQL database using Secure Infrastructure Access authentication."""
    if debug:
        logging.disable(logging.NOTSET)
        
    identity_handler = IdentityHandler()
    if not identity_handler.access_token:
        raise click.ClickException(
            "No valid login session found. Please run 'agc idp login' first."
        )
    
    try:
        # Initialize SIA handler and get credentials
        sia_handler = SecureInfraAccessHandler(tenant_id=tenant_id, 
                                               access_token=identity_handler.access_token)
        password = sia_handler.get_short_lived_password()
        
        # Construct the connection string
        # Format: postgresql://<username>#<tenant_id>@<host>:<password>@<host>/<database>
        sia_username = f"{username}#{tenant_id}@{db_host}"
        target_host = f"{tenant_id}.postgres.integration-cyberark.cloud"

        connection_string = f"postgresql://{target_host}:5432/{database}?user={quote_plus(sia_username)}&password={quote_plus(password)}&sslmode=require"

        logger.debug(f"Starting Postgres MCP server for database: {database} on host: {db_host}")

        # Run the postgres MCP server through the proxy
        argv = ("uvx", "postgres-mcp", "--access-mode=restricted", connection_string))
        asyncio.run(_stdio_mcp_proxy_async(
            argv=argv,
            cap=[ProxyCapability.AUDIT],
            secret_uris=[],
            is_debug=debug
        ))
        
    except Exception as e:
        raise click.ClickException(f"Failed to start Postgres MCP server: {str(e)}")
