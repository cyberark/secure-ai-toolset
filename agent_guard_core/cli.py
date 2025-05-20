import click

from agent_guard_core.config.config_manager import ConfigManager, ConfigurationOptions, SecretProviderOptions

# Retrieve the list of supported secret providers and the default provider.
provider_list = SecretProviderOptions.get_secret_provider_keys()
default_provider = SecretProviderOptions.get_default_secret_provider()


@click.group()
def cli():
    """
    Entry point for the Agent Guard CLI.
    """


@click.group()
def configure():
    """
    Commands to manage Agent Guard configuration.
    """


@configure.command()
@click.option(
    '--provider',
    default=default_provider,
    prompt=True,
    type=click.Choice(provider_list),
    help=('The secret provider to store and retrieve secrets.\n'
          f'Choose from: {provider_list}'),
)
@click.option('--conjur_authn_login',
              required=False,
              help="Conjur authentication login (workload ID).")
@click.option('--conjur_authn_api_key',
              required=False,
              help="API Key to authenticate to Conjur Cloud.")
@click.option('--conjur_appliance_url',
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


cli.add_command(configure)

if __name__ == '__main__':
    cli()
