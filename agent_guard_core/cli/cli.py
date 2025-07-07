import functools
import logging
import sys
from typing import Optional

import click

from agent_guard_core.cli.mcp_proxy import mcp_proxy
from agent_guard_core.cli.secrets import secrets
from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions
from agent_guard_core.credentials.enum import AwsEnvVars, ConjurEnvVars, CredentialsProvider, GcpEnvVars

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

provider_list = [provider.value for provider in CredentialsProvider]

@click.group(help=(
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options.")
    )
def cli():
    """Entry point for the Agent Guard CLI."""
    
@click.group(name="config")
def config():
    """Commands to manage Agent Guard configuration."""

def config_provider_option(func):
    @click.option('--provider', type=click.Choice(provider_list), help='Secret provider type')
    @functools.wraps(func)
    def wrapper(*args, provider=None, **kwargs):
        return func(*args, provider=provider, **kwargs)
    return wrapper

def config_conjur_options(func):
    @click.option('--conjur-authn-login', help='Conjur authentication login (workload ID)')
    @click.option('--conjur-appliance-url', help='Endpoint URL of Conjur Cloud')
    @click.option('--conjur-authenticator-id', help='Authenticator ID')
    @click.option('--conjur-account', help='Account ID')
    @click.option('--conjur-api-key', help='Conjur API key')
    @functools.wraps(func)
    def wrapper(*args,
                conjur_authn_login: Optional[str] = None,
                conjur_appliance_url: Optional[str] = None,
                conjur_authenticator_id: Optional[str] = None,
                conjur_account: Optional[str] = None,
                conjur_api_key: Optional[str] = None,
                **kwargs):
        config_manager = ConfigManager()
        
        if conjur_authn_login:
            config_manager.set_config_value(ConjurEnvVars.CONJUR_AUTHN_LOGIN, conjur_authn_login)
            
        if conjur_appliance_url:
            config_manager.set_config_value(ConjurEnvVars.CONJUR_APPLIANCE_URL, conjur_appliance_url)
            
        if conjur_authenticator_id:
            config_manager.set_config_value(ConjurEnvVars.CONJUR_AUTHENTICATOR_ID, conjur_authenticator_id)
            
        if conjur_account:
            config_manager.set_config_value(ConjurEnvVars.CONJUR_ACCOUNT, conjur_account)
            
        if conjur_api_key:
            config_manager.set_config_value(ConjurEnvVars.CONJUR_API_KEY, conjur_api_key)
            
        return func(*args, **kwargs)
    return wrapper

def config_aws_options(func):
    @click.option('--aws-region', help='AWS region')
    @click.option('--aws-access-key-id', help='AWS access key ID')
    @click.option('--aws-secret-access-key', help='AWS secret access key', hide_input=True)
    @functools.wraps(func)
    def wrapper(*args,
                aws_region: Optional[str] = None,
                aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None,
                **kwargs):
        config_manager = ConfigManager()
        
        if aws_region:
            config_manager.set_config_value(AwsEnvVars.AWS_REGION, aws_region)
            
        if aws_access_key_id:
            config_manager.set_config_value(AwsEnvVars.AWS_ACCESS_KEY_ID, aws_access_key_id)
            
        if aws_secret_access_key:
            config_manager.set_config_value(AwsEnvVars.AWS_SECRET_ACCESS_KEY, aws_secret_access_key)
            
        return func(*args, **kwargs)
    return wrapper

def config_gcp_options(func):
    @click.option('--gcp-project-id', help='GCP project ID')
    @click.option('--gcp-secret-id', help='GCP secret ID')
    @click.option('--gcp-region', help='GCP region')
    @click.option('--gcp-replication-type', help='GCP replication type: automatic or user-managed')
    @functools.wraps(func)
    def wrapper(*args,
                gcp_project_id: Optional[str] = None,
                gcp_secret_id: Optional[str] = None,
                gcp_region: Optional[str] = None,
                gcp_replication_type: Optional[str] = None,
                **kwargs):
        config_manager = ConfigManager()
        
        if gcp_project_id:
            config_manager.set_config_value(GcpEnvVars.GCP_PROJECT_ID, gcp_project_id)
            
        if gcp_secret_id:
            config_manager.set_config_value(GcpEnvVars.GCP_SECRET_ID, gcp_secret_id)
            
        if gcp_region:
            config_manager.set_config_value(GcpEnvVars.GCP_REGION, gcp_region)
            
        if gcp_replication_type:
            config_manager.set_config_value(GcpEnvVars.GCP_REPLICATION_TYPE, gcp_replication_type)
            
        return func(*args, **kwargs)
    return wrapper

@config.command(name="set")
@config_provider_option
@config_conjur_options
@config_aws_options
@config_gcp_options
def config_set(provider, **kwargs):
    """Set configuration values"""
    config_manager = ConfigManager()
    if provider:
        config_manager.set_config_value(ConfigurationOptions.SECRET_PROVIDER.name, provider)
    
    click.echo("Configuration updated successfully")

@config.command(name="get")
@click.option('--key', type=click.Choice(
    [item.name for item in ConfigurationOptions] + ['CONJUR_AUTHN_LOGIN']), 
    required=True, help='Configuration key to retrieve')
def config_get(key):
    """Get a configuration value"""
    config_manager = ConfigManager()
    value = config_manager.get_config_value(key)
    if value:
        click.echo(f"{key}={value}")
    else:
        click.echo(f"No value set for {key}")

@config.command('list')
def config_list():
    """List all configuration values"""
    config_manager = ConfigManager()
    config_dict = config_manager.get_config()
    click.echo("Agent Guard Configuration:")
    for key, value in config_dict.items():
        click.echo(f"{key}={value}")

# Register the config group with the main CLI
cli.add_command(config)
cli.add_command(secrets)
cli.add_command(mcp_proxy)

if __name__ == '__main__':
    try:
        # TODO: remove this
        # cli(["secrets", "get", "-p", "aws-secretsmanager", "-k" ,"weather_api_key_2", "-n", "default/agentic_env_vars"], standalone_mode=False)  # Use empty list to avoid click's default behavior of parsing sys.argv
        cli(sys.argv[1:], standalone_mode=False)
    except KeyboardInterrupt:
        logger.debug("KeyboardInterrupt caught at top level, exiting gracefully.")
        print("\nExiting Agent Guard CLI.")
        sys.exit(0)