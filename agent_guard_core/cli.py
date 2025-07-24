import click

from agent_guard_core.cli.login_idp import idp_login
from agent_guard_core.cli.mcp_proxy_cli import mcp_proxy
from agent_guard_core.cli.sia_postgresdb_cli import sia_postgresdb


@click.group()
def cli():
    """Agent Guard CLI tools."""
    pass

cli.add_command(idp_login)
cli.add_command(mcp_proxy)
cli.add_command(sia_postgresdb)

if __name__ == '__main__':
    cli()
