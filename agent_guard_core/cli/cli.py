import functools
import logging
import os
import sys
from typing import Any, Optional

import click

from agent_guard_core.cli.mcp_proxy import mcp_proxy
from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions
from agent_guard_core.credentials.enum import AwsEnvVars, ConjurEnvVars, CredentialsProvider, GcpEnvVars
from agent_guard_core.credentials.gcp_secrets_manager_provider import DEFAULT_PROJECT_ID, DEFAULT_REPLICATION_TYPE
from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider, secrets_provider_fm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group(help=(
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options.")
    )
def cli():
    """Entry point for the Agent Guard CLI."""
    
@click.group(name="config")
def config():
    """Commands to manage Agent Guard configuration."""

@click.group(name="secrets")
def secrets():
    """Commands to manage secrets in Agent Guard."""

default_provider = ConfigManager().get_config_value(
    ConfigurationOptions.SECRET_PROVIDER.value
) or CredentialsProvider.AWS_SECRETS_MANAGER

provider_list = [provider.value for provider in CredentialsProvider]

def provider_option(f):
    return click.option('--provider', '-p', 
                        required=True, type=click.Choice(provider_list), 
                        help=('The secret provider to store and retrieve secrets.\n'
          f'Choose from: {provider_list}'))(f)

def secret_name_option(f):
    return click.option('--secret_key', '-k', 
                        required=True, help='The name of the secret to store or retrieve.')(f)

def secret_value_option(f):
    return click.option('--secret_value', '-v', 
                        required=True, help='The value of the secret to store.')(f)

def namespace_option(f):
    return click.option('--namespace', '-n', 
                        required=False, help='The name of the namespace to use')(f)

def gcp_options(func):
    @click.option('--gcp-project-id', '-gp', required=False, help='GCP project ID')
    @click.option('--gcp-secret-id', '-gs', required=False, help='GCP secret ID')
    @click.option('--gcp-region', '-gr', required=False, help='GCP secret region (required for user-managed replication)')
    @click.option('--gcp-replication-type', '-gt', required=False, help='GCP replication type: automatic or user-managed')
    @functools.wraps(func)
    def wrapper(*args,
                gcp_project_id: Optional[str] = None,
                gcp_secret_id: Optional[str] = None,
                gcp_region: Optional[str] = None,
                gcp_replication_type: Optional[str] = None,
                **kwargs):
        provider = kwargs.get('provider')
        if provider == CredentialsProvider.GCP_SECRETS_MANAGER:
            os.environ[GcpEnvVars.GCP_PROJECT_ID] = gcp_project_id or os.environ.get(GcpEnvVars.GCP_PROJECT_ID, DEFAULT_PROJECT_ID)
            os.environ[GcpEnvVars.GCP_SECRET_ID] = gcp_secret_id or os.environ.get(GcpEnvVars.GCP_SECRET_ID, None)
            os.environ[GcpEnvVars.GCP_REGION] = gcp_region or os.environ.get(GcpEnvVars.GCP_REGION, None)
            os.environ[GcpEnvVars.GCP_REPLICATION_TYPE] = gcp_replication_type or os.environ.get(GcpEnvVars.GCP_REPLICATION_TYPE, DEFAULT_REPLICATION_TYPE)

            # Region required if replication is user-managed
            if os.environ[GcpEnvVars.GCP_REPLICATION_TYPE] == "user-managed" and not os.environ[GcpEnvVars.GCP_REGION]:
                raise click.UsageError("GCP region is required for user-managed replication.")

        return func(*args, **kwargs)

    return wrapper


def conjur_options(func):
    @click.option('--conjur-authn-login', '-cl', required=False, help='Conjur authentication login (workload ID).')
    @click.option('--conjur-appliance-url', '-cu', required=False, help='Endpoint URL of Conjur Cloud.')
    @click.option('--conjur-authenticator-id', '-ci', required=False, help='Authenticator ID')
    @click.option('--conjur-account', '-ca', required=False, help='Account ID')
    @click.option('--conjur-api-key', '-ck', required=False, help='Conjur API key.')
    @functools.wraps(func)
    def wrapper(*args, conjur_authn_login: Optional[str] = None, 
                conjur_appliance_url: Optional[str] = None, 
                conjur_authenticator_id: Optional[str] = None,
                conjur_account: Optional[str] = None,
                conjur_api_key: Optional[bool] = None, **kwargs):
        provider = kwargs.get('provider')
        if provider == CredentialsProvider.CONJUR:            
            os.environ[ConjurEnvVars.CONJUR_AUTHN_LOGIN] = os.environ.get(ConjurEnvVars.CONJUR_AUTHN_LOGIN, conjur_authn_login)
            os.environ[ConjurEnvVars.CONJUR_APPLIANCE_URL] = os.environ.get(ConjurEnvVars.CONJUR_APPLIANCE_URL, conjur_appliance_url)
            os.environ[ConjurEnvVars.CONJUR_AUTHENTICATOR_ID] = os.environ.get(ConjurEnvVars.CONJUR_AUTHENTICATOR_ID, conjur_authenticator_id)
            os.environ[ConjurEnvVars.CONJUR_ACCOUNT] = os.environ.get(ConjurEnvVars.CONJUR_ACCOUNT, conjur_account)
            os.environ[ConjurEnvVars.CONJUR_API_KEY] = os.environ.get(ConjurEnvVars.CONJUR_API_KEY, conjur_api_key)

            mandatory_env_vars = [ConjurEnvVars.CONJUR_AUTHN_LOGIN, 
                                  ConjurEnvVars.CONJUR_APPLIANCE_URL, 
                                  ConjurEnvVars.CONJUR_AUTHENTICATOR_ID, 
                                  ConjurEnvVars.CONJUR_API_KEY]
            
            if any(os.environ.get(env_var) is None for env_var in mandatory_env_vars):
                raise click.UsageError(
                    "conjur-auth-login, conjur-appliance-url, "
                    "conjur-authenticator-id, and conjur-api-key are required for Conjur provider.")

        return func(*args, **kwargs)
    return wrapper


def aws_options(func):
    @click.option('--aws-region', '-ar', required=False, help='AWS region')
    @click.option('--aws-access-key-id', '-ak', required=False, help='AWS access key ID')
    @click.option('--aws-secret-access-key', '-as', required=False, help='AWS secret access key')
    @functools.wraps(func)
    def wrapper(*args,
                aws_region: Optional[str] = None,
                aws_access_key_id: Optional[str] = None,
                aws_secret_access_key: Optional[str] = None,
                **kwargs):
        provider = kwargs.get('provider')
        if provider == CredentialsProvider.AWS_SECRETS_MANAGER:
            # Get values from env if not passed
            aws_region = aws_region or os.environ.get(AwsEnvVars.AWS_REGION)
            aws_access_key_id = aws_access_key_id or os.environ.get(AwsEnvVars.AWS_ACCESS_KEY_ID)
            aws_secret_access_key = aws_secret_access_key or os.environ.get(AwsEnvVars.AWS_SECRET_ACCESS_KEY)

            if aws_region:
                os.environ[AwsEnvVars.AWS_REGION] = aws_region
            if aws_access_key_id:
                os.environ[AwsEnvVars.AWS_ACCESS_KEY_ID] = aws_access_key_id
            if aws_secret_access_key:
                os.environ[AwsEnvVars.AWS_SECRET_ACCESS_KEY] = aws_secret_access_key

        return func(*args, **kwargs)
    return wrapper


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


@secrets.command()
@provider_option
@secret_name_option
@secret_value_option
@namespace_option
@aws_options
@conjur_options
@gcp_options
def set(provider, secret_key, secret_value, namespace):
    """
    Set a secret in a provider using Agent Guard.

    This command allows you to to set a secret in the specified secret provider.
    If no provider is specified, it will prompt you to select one from the available options.
    """
    extra: dict[str, Any] = {}
    if namespace:
        extra['namespace'] = namespace

    provider: BaseSecretsProvider = secrets_provider_fm.get(provider)(**extra)
    if not provider.connect():
        raise click.ClickException(f"Failed to connect to provider: {provider}")
    
    provider.store(key=secret_key, secret=secret_value)
    
@secrets.command()
@provider_option
@secret_name_option
@namespace_option
@aws_options
@conjur_options
@gcp_options
def get(provider, secret_key, namespace):
    """
    Get a secret from a provider using Agent Guard.

    This command allows you to to get a secret from the specified secret provider.
    If no provider is specified, it will prompt you to select one from the available options.
    """
    extra: dict[str, Any] = {}
    if namespace:
        extra['namespace'] = namespace

    provider: BaseSecretsProvider = secrets_provider_fm.get(provider)(**extra)
    if not provider.connect():
        raise click.ClickException(f"Failed to connect to provider: {provider}")
    
    secret = provider.get(key=secret_key)
    if secret is None:
        raise click.ClickException(f"Failed to retrieve secret {secret_key} from provider: {provider}")

    print(secret, end='')


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