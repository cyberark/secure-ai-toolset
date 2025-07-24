
import asyncio
import json
import logging
import os
import sys
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote_plus

import click
from mcp import ClientSession, StdioServerParameters, stdio_client, stdio_server

from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider, secrets_provider_fm
from agent_guard_core.model.secret_uri import SecretUri, SecretUriList
from agent_guard_core.proxy.audited_proxy import create_agent_guard_proxy_server
from agent_guard_core.proxy.proxy_utils import get_audit_logger
from agent_guard_core.utils.mcp_config_wizard import transform_mcp_servers

logger = logging.getLogger(__name__)

class ProxyCapability(str, Enum):
    AUDIT = "audit"


cap_options = click.Choice([e.value for e in ProxyCapability])

def cap_option(f) -> Any:
    return click.option("--cap", "-c", type=cap_options, help="Enable specific capabilities for the MCP proxy. Use multiple -c"
                                                              f"options to enable multiple capabilities. One of: {' '.join(cap_options.choices)}", 
                                                              multiple=True)(f)

def secret_uri_option(f) -> Any:
    return click.option(
        '--secret-uri',
        '-s',
        help="Secret URI to fetch credentials from. Format: <provider>://<key>[/<env_var>]. "
             "Example: conjur://mysecret/MY_ENV_VAR",
        type=str,
        required=False,
        multiple=True
    )(f)

def get_secrets_from_env_option(f) -> Any:
    return click.option(
        '--get-secrets-from-env',
        '-si',
        is_flag=True,
        required=False,
        default=False,
        help="Fetch secrets from environment variables. "
             "If set, will use all environment variables that match the format <env_var>=<provider>://<key>. "
             "Example: MY_ENV_VAR=conjur://mysecret"
    )(f)

@click.group(help="Commands to manage Agent Guard MCP proxy.")
def mcp_proxy() -> Any:
    pass


@mcp_proxy.command(name="start", help="Starts the Agent Guard MCP proxy")
@click.option(
    '--debug',
    '-d','is_debug',
    is_flag=True,
    required=False,
    default=False,
    help="debug mode"
)
@cap_option
@secret_uri_option
@get_secrets_from_env_option
@click.argument('argv', nargs=-1)
def mcp_proxy_start(is_debug: bool = False, 
                    cap: Optional[list[ProxyCapability]] = None, 
                    secret_uri: Optional[list[str]] = None,
                    get_secrets_from_env: bool = False,
                    argv: tuple[str] = ()):
    if cap is None:
        cap = []
    if secret_uri is None:
        secret_uri = []

    if is_debug:
        logging.disable(logging.NOTSET)
        
    asyncio.run(_stdio_mcp_proxy_async(argv=argv, cap=cap, secret_uris=secret_uri, get_secrets_from_env=get_secrets_from_env, is_debug=is_debug))

async def _stdio_mcp_proxy_async(cap: list[ProxyCapability], 
                                 secret_uris: list[str],
                                 get_secrets_from_env: bool = False,
                                 argv: tuple[str] = (), 
                                 is_debug: bool = False
                                 ):
    session_id = uuid.uuid4().hex
    logger.debug(f"Starting up oroxy with session id {session_id}")
    stdio_params: Optional[StdioServerParameters] = None
    
    if len(argv) == 0:
        raise click.BadArgumentUsage("Please provide a valid CLI to start an MCP server (i.e uvx mcp-server-fetch)")
    
    stdio_params = StdioServerParameters(command=argv[0], args=argv[1:])
    proxy_logger: Optional[logging.Logger] = None

    if get_secrets_from_env:
        logger.debug("Fetching secrets from environment variables.")
        parsed_secret_uris = SecretUriList.from_env_vars(list(os.environ.items()))
        secret_uris = [*secret_uris, *parsed_secret_uris.root] if secret_uris else parsed_secret_uris.root
        
        if not secret_uris:
            logger.warning("No valid secret URIs found in environment variables. Please set them in the format: MY_ENV_VAR=conjur://mysecret")
    
    if secret_uris:
        logger.debug(f"Using secret URIs: {secret_uris}")
        apply_secrets(secret_uris)

    if ProxyCapability.AUDIT in cap:
        logger.debug("Enabling audit logging for the MCP proxy.")
        proxy_logger = get_audit_logger(session_id=session_id, log_level=logging.DEBUG if is_debug else logging.INFO)
    try:
        logger.debug(f"Starting MCP server with config: {stdio_params.model_dump()}")
        async with stdio_client(stdio_params, errlog=sys.stderr) as streams, ClientSession(*streams) as session:
            app = await create_agent_guard_proxy_server(remote_app=session, audit_logger=proxy_logger)
            async with stdio_server() as (read_stream, write_stream):
                logger.debug("Proxy server is running...")
                await app.run(
                    read_stream,
                    write_stream,
                    app.create_initialization_options()
                )
                logger.debug("Proxy server has stopped.")
    except Exception as e:
        logger.error(f"Error starting Agent Guard proxy: {e}")
    except (asyncio.CancelledError, KeyboardInterrupt) as e:
        logger.debug("Caught CancelledError due to KeyboardInterrupt, exiting gracefully.")
        sys.exit(0)

@mcp_proxy.command(name="apply-config", context_settings=dict(max_content_width=120))
@click.option(
    '--mcp-config-file',
    '-cf',
    required=False,
    help="Path to the MCP configuration file, Default: Auto-detect under /config/*.json (use docker -v to mount a local directory to /config)",
)
@cap_option
def proxy_apply_config(mcp_config_file: Optional[str] = None, cap: Optional[tuple[str]] = None):
    """
    Generates an Agent-Guard-Proxy-Enabled configuration from
    an existing MCP configuration file (i.e Claude Desktop, Claude Code, etc.)
    """
    if cap is None:
        cap = []
        
    if mcp_config_file is None:
        # Search for a json file under /config
        config_dir = Path("/config")
        if not config_dir.exists() or not config_dir.is_dir():
            logger.error("No /config directory found or it is not a directory.")
            sys.exit(1)

        for config_file in config_dir.glob("*.json"):
            try:
                new_mcp_configuration = transform_mcp_servers(config_file, capabilities=cap)
                logger.debug(f"Converted MCP configuration at: {config_file}")
                print(json.dumps(new_mcp_configuration, indent=2))
            except Exception as ex:
                logger.debug(f"Error reading MCP config file {config_file}: {ex}")
                continue

def apply_secrets(secret_uris: list[str]) -> None:
    provider_map: dict[str, BaseSecretsProvider] = {}

    for uri in secret_uris:
        secret_uri: Optional[SecretUri] = None

        try:
            if isinstance(uri, str):
                secret_uri = SecretUri.from_uri(uri)
            elif isinstance(uri, SecretUri):
                secret_uri = uri
        except Exception as e:
            logger.warning(f"Failed to parse secret URI '{uri}': {e}")
            continue
        
        try:
            provider = provider_map.setdefault(secret_uri.provider, secrets_provider_fm.get(secret_uri.provider)())

            if not provider.connect():
                raise click.ClickException(f"Failed to connect to provider: {provider}")
            
            secret = provider.get(key=secret_uri.key)
            if secret is None:
                logger.warning(f"Secret '{secret_uri.key}' not found in provider '{secret_uri.provider}'")
                continue
        except Exception as e:
            logger.error(f"Error retrieving secret '{secret_uri.key}' from provider '{secret_uri.provider}': {e}")
            continue

        logger.debug(f"Setting environment variable '{secret_uri.env_var}' with secret value")
        os.environ[secret_uri.env_var] = secret