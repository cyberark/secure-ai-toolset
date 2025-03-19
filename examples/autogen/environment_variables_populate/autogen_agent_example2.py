import asyncio
import os
from typing import List

from autogen_core import AgentId, SingleThreadedAgentRuntime
from autogen_core.tool_agent import ToolAgent
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from examples.autogen.environment_variables_populate.autogen_common import Message, ToolUseAgent, get_stock_price
from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.environment_manager import EnvironmentVariablesManager


async def main() -> None:
    """
    The main function to run the agent.
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
                model='gpt-4o',
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                azure_deployment='gpt-4o',
                api_version='2024-02-01',
                api_key=os.getenv('AZURE_OPENAI_KEY')),
            [tool.schema for tool in tools], 'tool_executor_agent'),
    )

    try:
        # Start processing messages.
        with EnvironmentVariablesManager(AWSSecretsProvider()):
            runtime.start()

            # Send a direct message to the tool agent.
            prompt = f"What is the stock price of NVDA on 2024/06/01? "
            tool_use_agent_id = AgentId(type="tool_use_agent", key="2")
            response = await runtime.send_message(Message(prompt),
                                                  tool_use_agent_id)
            print(response.content)

    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        try:
            # Stop processing messages.
            await runtime.stop()
        except Exception as e:
            print(f'An error occurred during cleanup: {e}')


if __name__ == '__main__':
    asyncio.run(main())
