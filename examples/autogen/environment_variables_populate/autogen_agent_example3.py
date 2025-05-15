import asyncio
import os
from typing import List

from autogen_core import SingleThreadedAgentRuntime
from autogen_core.tool_agent import ToolAgent
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from agent_guard_core.credentials.gcp_secrets_manager_provider import GCPSecretsProvider
from examples.autogen.environment_variables_populate.autogen_common import ToolUseAgent, get_stock_price


@EnvironmentVariablesManager.set_env_vars(
    GCPSecretsProvider(
        project_id="sample-project-id",
        secret_id="sample-secret-id",
    ))
async def main() -> None:
    """
    The main function to run the agent using GCP Secret Manager for environment variables.

    This example demonstrates how to use GCP Secret Manager as the secrets provider
    for managing environment variables in an AutoGen agent setup.

    Prerequisites:
    1. GCP project set up with Secret Manager API enabled
    2. Service account with Secret Manager access
    3. GOOGLE_APPLICATION_CREDENTIALS environment variable set to service account key file
    4. Required secrets stored in GCP Secret Manager

    The example shows two types of secrets:
    1. Cross-regional secrets (automatically replicated across regions)
       - Path format: projects/{project_id}/secrets/{secret_id}
       - Example: projects/857072587832/secrets/cross_region_secrets

    2. Regional secrets (stored in specific regions)
       - Path format: projects/{project_id}/locations/{region}/secrets/{secret_id}
       - Example: projects/857072587832/locations/us-central1/secrets/regional_secrets
    """
    # Create a runtime.
    runtime = SingleThreadedAgentRuntime()

    # Create the tools.
    tools: List[Tool] = [
        FunctionTool(get_stock_price, description='Get the stock price.')
    ]

    # Register the agents.
    await ToolAgent.register(runtime, 'tool_executor_agent',
                             lambda: ToolAgent('tool executor agent', tools))

    await ToolUseAgent.register(
        runtime,
        'tool_use_agent',
        lambda: ToolUseAgent(
            AzureOpenAIChatCompletionClient(
                model='gpt-4',
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                azure_deployment='gpt-4',
                api_version='2024-02-01'), [tool.schema for tool in tools],
            'tool_executor_agent'),
    )

    try:
        # Start processing messages.
        runtime.start()

        # Example 1: Cross-regional secrets (automatically replicated)
        cross_region_provider = GCPSecretsProvider(
            project_id="857072587832",
            secret_id="cross_region_secrets",
            replication_type="automatic")
        cross_region_provider.store("AZURE_OPENAI_ENDPOINT",
                                    "your-azure-endpoint")
        cross_region_provider.store("AZURE_OPENAI_API_KEY",
                                    "your-azure-api-key")

        # Example 2: Regional secrets (user-managed replication)
        regional_provider = GCPSecretsProvider(
            project_id="857072587832",
            secret_id="regional_secrets",
            region="us-central1",
            replication_type="user_managed",
            replication_locations=["us-central1", "us-west1"])
        regional_provider.store("DATABASE_URL", "your-database-url")
        regional_provider.store("API_KEY", "your-api-key")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        runtime.stop()


if __name__ == "__main__":
    asyncio.run(main())
