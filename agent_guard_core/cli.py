import click

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions, SecretProviderOptions

# Retrieve the list of supported secret providers and the default provider.


@click.group(
    help=
    "Agent Guard CLI: Secure your AI agents with environment credentials from multiple secret providers.\n"
    "Use 'configure' to manage configuration options.")
def cli():
    """
    Entry point for the Agent Guard CLI.
    """


@click.group()
def configure():
    """
    Commands to manage Agent Guard configuration.
    """


provider_list = SecretProviderOptions.get_keys()


@configure.command()
@click.option(
    '--provider',
    '-p',
    default=SecretProviderOptions.get_default(),
    prompt=True,
    type=click.Choice(provider_list),
    help=('The secret provider to store and retrieve secrets.\n'
          f'Choose from: {provider_list}'),
)
@click.option('--conjur-authn-login',
              '-cl',
              required=False,
              help="Conjur authentication login (workload ID).")
@click.option('--conjur-authn-api-key',
              '-ck',
              required=False,
              prompt=True,
              help="API Key to authenticate to Conjur Cloud.")
@click.option('--conjur-appliance-url',
              '-cu',
              required=False,
              help="Endpoint URL of Conjur Cloud.")
def set(provider, conjur_authn_login, conjur_authn_api_key,
        conjur_appliance_url):
    """
    Set the secret provider and related Conjur options in the Agent Guard configuration.

    You can specify the provider and, if using Conjur, provide additional authentication details.
    """
    config_manager = ConfigManager()
    config_manager.set_config_value(
        key=ConfigurationOptions.SECRET_PROVIDER.name, value=provider)
    if conjur_authn_login:
        config_manager.set_config_value(
            key=ConfigurationOptions.CONJUR_AUTHN_LOGIN.name,
            value=conjur_authn_login)
    if conjur_authn_api_key:
        config_manager.set_config_value(
            key=ConfigurationOptions.CONJUR_AUTHN_API_KEY.name,
            value=conjur_authn_api_key)
    if conjur_appliance_url:
        config_manager.set_config_value(
            key=ConfigurationOptions.CONJUR_APPLIANCE_URL.name,
            value=conjur_appliance_url)


@configure.command('list')
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


@configure.command('get')
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


cli.add_command(configure)


def main():
    cli()


if __name__ == '__main__':
    main()
