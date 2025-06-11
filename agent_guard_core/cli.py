import functools
import os
from typing import Any, Optional

import click

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions, SecretProviderOptions
from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider
from agent_guard_core.credentials.gcp_secrets_manager_provider import (DEFAULT_PROJECT_ID, DEFAULT_REPLICATION_TYPE,
                                                                       DEFAULT_SECRET_ID, GCPSecretsProvider)
from agent_guard_core.credentials.secrets_provider import BaseSecretsProvider

PROVIDER_MAP: dict[str, BaseSecretsProvider] = {
    SecretProviderOptions.AWS_SECRETS_MANAGER_PROVIDER.name: AWSSecretsProvider,
    SecretProviderOptions.FILE_SECRET_PROVIDER.name: FileSecretsProvider,
    SecretProviderOptions.CONJUR_SECRET_PROVIDER.name: ConjurSecretsProvider,
    SecretProviderOptions.GCP_SECRET_PROVIDER.name: GCPSecretsProvider,
}

@click.group(help=(
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options."))
def cli():
    """Entry point for the Agent Guard CLI."""


@click.group(name="config")
def config():
    """Commands to manage Agent Guard configuration."""

@click.group(name="secrets")
def secrets():
    """Commands to manage secrets in Agent Guard."""

provider_list = SecretProviderOptions.get_keys()

default_provider = ConfigManager().get_config_value(
    ConfigurationOptions.SECRET_PROVIDER.name
) or SecretProviderOptions.get_default()

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
        if provider == SecretProviderOptions.GCP_SECRET_PROVIDER.name:
            # Get values from env if not passed
            gcp_project_id = gcp_project_id or os.environ.get('GCP_PROJECT_ID', DEFAULT_PROJECT_ID)
            gcp_secret_id = gcp_secret_id or os.environ.get('GCP_SECRET_ID', DEFAULT_SECRET_ID)
            gcp_region = gcp_region or os.environ.get('GCP_REGION')
            gcp_replication_type = gcp_replication_type or os.environ.get('GCP_REPLICATION_TYPE', DEFAULT_REPLICATION_TYPE)

            # Region required if replication is user-managed
            if gcp_replication_type == "user-managed" and not gcp_region:
                raise click.UsageError("GCP region is required for user-managed replication.")

            os.environ['GCP_PROJECT_ID'] = gcp_project_id
            os.environ['GCP_SECRET_ID'] = gcp_secret_id
            os.environ['GCP_REGION'] = gcp_region or ''
            os.environ['GCP_REPLICATION_TYPE'] = gcp_replication_type
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
        if provider == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name:
            conjur_authn_login = os.environ.get('CONJUR_AUTHN_LOGIN', conjur_authn_login)
            conjur_appliance_url = os.environ.get('CONJUR_APPLIANCE_URL', conjur_appliance_url)
            conjur_authenticator_id = os.environ.get('CONJUR_AUTHENTICATOR_ID', conjur_authenticator_id)
            conjur_account = os.environ.get('CONJUR_ACCOUNT', conjur_account)
            conjur_api_key = os.environ.get('CONJUR_API_KEY', conjur_api_key)

            if any(param is None for param in [conjur_authn_login, conjur_appliance_url, 
                                               conjur_authenticator_id, conjur_api_key]):
                raise click.UsageError(
                    "conjur-auth-login, conjur-appliance-url, "
                    "conjur-authenticator-id, and conjur-api-key are required for Conjur provider.")
            
            os.environ['CONJUR_AUTHN_LOGIN'] = conjur_authn_login
            os.environ['CONJUR_APPLIANCE_URL'] = conjur_appliance_url
            os.environ['CONJUR_AUTHENTICATOR_ID'] = conjur_authenticator_id
            os.environ['CONJUR_ACCOUNT'] = conjur_account
            os.environ['CONJUR_API_KEY'] = conjur_api_key

        return func(*args, **kwargs)
    return wrapper


@secrets.command()
@provider_option
@secret_name_option
@secret_value_option
@namespace_option
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

    provider: BaseSecretsProvider = PROVIDER_MAP.get(provider)(**extra)
    if not provider.connect():
        raise click.ClickException(f"Failed to connect to provider: {provider}")
    
    provider.store(key=secret_key, secret=secret_value)
    
@secrets.command()
@provider_option
@secret_name_option
@namespace_option
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

    provider: BaseSecretsProvider = PROVIDER_MAP.get(provider)(**extra)
    if not provider.connect():
        raise click.ClickException(f"Failed to connect to provider: {provider}")
    
    secret = provider.get(key=secret_key)
    if secret is None:
        raise click.ClickException(f"Failed to retrieve secret {secret_key} from provider: {provider}")

    print(secret, end='')


@config.command('list')
def list_params():
    """
    List all configuration parameters and their values for Agent Guard.

    Displays the current configuration as key-value pairs.
    """
    config_manager = ConfigManager()
    config = config_manager.get_config()
    click.echo("Agent Guard Configuration:")
    if config:
        for k, v in config.items():
            click.echo(f"  {k}={v}")
    else:
        click.echo("  No configuration found.")


@config.command('get')
@click.option(
    '--key',
    required=False,
    prompt=True,
    default=ConfigurationOptions.get_default(),
    type=click.Choice(ConfigurationOptions.get_keys()),
    help=
    "The configuration parameter key to retrieve (e.g., SECRET_PROVIDER, CONJUR_AUTHN_LOGIN, etc.)."
)
def get_param(key):
    """
    Get the value of a specific configuration parameter by key.
    """
    config_manager = ConfigManager()
    config = config_manager.get_config()
    value = config.get(key)
    if value is not None:
        click.echo(f"{key}={value}")
    else:
        click.echo(f"No value found for key: {key}")


cli.add_command(config)
cli.add_command(secrets)