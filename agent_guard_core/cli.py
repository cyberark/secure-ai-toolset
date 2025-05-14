#!/usr/bin/env python
import click

def print_header(message):
    click.echo( '+' + '-' * (len(message) - 2) + '+' )
    click.echo( '|' + message[1:-1] + '|' )
    click.echo( '+' + '-' * (len(message) - 2) + '+' )



#########################
# Secret commands 
#########################
@click.group(help='Commands related to secrets management')
def secrets():
    pass

@secrets.command(help='Create secret')
@click.argument('key')
@click.argument('value')
def create(key, value):
    click.echo(f"Creating secret {key} with value {value}")

@secrets.command(help='Delete secret')
@click.argument('key')
def delete(key):
    click.echo(f"Deleting secret {key}")

#########################
# Config commands 
#########################
@click.group(help='Commands related to configuration')
def config():
    pass

@config.command(help='Set configuration parameters')
@click.argument('key')
@click.argument('value')
@click.option('--global', 'is_global', is_flag=True, help='Set configuration globally')
@click.option('--local', 'is_local', is_flag=True, help='Set configuration locally (default)')
def set(key, value, is_global, is_local):
    scope = "globally" if is_global else "locally"
    click.echo(f"Setting {key}={value} {scope}")
    
    # Special handling for secret-provider configuration
    if key == "secret-provider":
        click.echo(f"Configuring secret provider: {value}")

@config.command(help='Get configuration parameter value')
@click.argument('key')
def get(key):
    click.echo(f"Getting configuration value for {key}")

@config.command(help='Display all configuration settings')
def info():
    print_header("Current Configuration Settings")

    # Placeholder for actual configuration display
    click.echo("secret-provider: <current-provider>")
    click.echo("other-settings: <value>")
    click.echo("-" * 30)

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx) -> None:
    if ctx.invoked_subcommand is None:
        print_header("Welcome to Agent Guard! Use --help to see available commands.")
        click.echo("\nUse 'python cli.py --help' to see available commands.")
    
# Add secrets as a subcommand of main
main.add_command(secrets)
# Add config as a subcommand of main
main.add_command(config)

if __name__ == "__main__":  # pragma: no cover
    main()