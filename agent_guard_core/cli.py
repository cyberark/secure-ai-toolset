import getpass

import click

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions, SecretProviderOptions


@click.group(help=(
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options."))
def cli():
    """Entry point for the Agent Guard CLI."""


@click.group(name="config")
def config():
    """Commands to manage Agent Guard configuration."""


provider_list = SecretProviderOptions.get_keys()

default_provider = ConfigManager().get_config_value(
    ConfigurationOptions.SECRET_PROVIDER.name
) or SecretProviderOptions.get_default()


@config.command()
@click.option(
    '--provider',
    '-p',
    default=default_provider,
    prompt=True,
    required=False,
    type=click.Choice(provider_list),
    help=('The secret provider to store and retrieve secrets.\n'
          f'Choose from: {provider_list}'),
)
@click.option('--conjur-authn-login',
              '-cl',
              required=False,
              help="Conjur authentication login (workload ID).")
@click.option('--conjur-appliance-url',
              '-cu',
              required=False,
              help="Endpoint URL of Conjur Cloud.")
@click.option('--conjur-api-key',
              '-ca',
              is_flag=True,
              help="Prompt for Conjur API Key.")
def set(provider, conjur_authn_login, conjur_appliance_url, conjur_api_key):
    """
    Set the secret provider and related options in the Agent Guard configuration.

    You can specify the provider and, if using a provider with sensitive parameters,
    those will always be prompted for securely.
    """
    config_manager = ConfigManager()

    existing_provider = config_manager.get_config_value(
        ConfigurationOptions.SECRET_PROVIDER)
    if not (provider or existing_provider):
        provider = click.prompt("Select secret provider",
                                type=click.Choice(provider_list),
                                show_choices=True)
    else:
        print(f"Provider: {provider}")

    config_manager.set_config_value(
        key=ConfigurationOptions.SECRET_PROVIDER.name, value=provider)

    if conjur_authn_login:
        config_manager.set_config_value(
            key=ConfigurationOptions.CONJUR_AUTHN_LOGIN.name,
            value=conjur_authn_login)

    if conjur_appliance_url:
        config_manager.set_config_value(
            key=ConfigurationOptions.CONJUR_APPLIANCE_URL.name,
            value=conjur_appliance_url)

    # Only prompt for API key if requested and provider is conjur
    if conjur_api_key:
        if provider.lower(
        ) == SecretProviderOptions.CONJUR_SECRET_PROVIDER.name.lower():
            sensitive_value = getpass.getpass(
                "Enter value for Conjur Authn Api Key: ")
            config_manager.set_config_value(key="CONJUR_AUTHN_API_KEY",
                                            value=sensitive_value)
        else:
            click.echo(
                "Warning: --conjur-api-key flag is only applicable when provider is 'conjur'. No value was set."
            )


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
