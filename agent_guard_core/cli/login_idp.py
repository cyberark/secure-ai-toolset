import logging
import sys

import click

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@click.group(name="idp-login")
def secrets():
    """Commands to manage IDP login in Agent Guard."""
