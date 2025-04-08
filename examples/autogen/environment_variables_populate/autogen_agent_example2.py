import asyncio
import os
from typing import List

from autogen_core import AgentId, SingleThreadedAgentRuntime
from autogen_core.tool_agent import ToolAgent
from autogen_core.tools import FunctionTool, Tool
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from agent_guard_core.credentials.conjur_secrets_provider import ConjurSecretsProvider
from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from examples.autogen.environment_variables_populate.autogen_common import Message, ToolUseAgent, get_stock_price


async def main() -> None:
    """
    The main function to run the agent.

    Steps:
    1. Create a runtime for managing agents.
    2. Define tools and register a ToolAgent to execute them.
    3. Register a ToolUseAgent that interacts with the ToolAgent using Azure OpenAI.
    4. Use EnvironmentVariablesManager to inject environment variables securely.
    5. Start the runtime and send a message to the ToolUseAgent to get a stock price.
    6. Print the response and handle any errors during execution.
    7. Ensure proper cleanup by stopping the runtime.
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
                api_version='2024-02-01'), [tool.schema for tool in tools],
            'tool_executor_agent'),
    )

    try:
        # Start processing messages.
        before_os_dict = os.environ.copy()
        with EnvironmentVariablesManager(ConjurSecretsProvider()):
            # Print the environment variables after injection
            new_keys = set(os.environ.keys()) - set(before_os_dict.keys())
            print("New environment keys after injection:")
            print("\n".join(new_keys))

            runtime.start()

            # Send a direct message to the tool agent.
            prompt = f"What is the stock price of NVDA on 2024/06/01? "
            tool_use_agent_id = AgentId(type="tool_use_agent", key="2")
            response = await runtime.send_message(Message(prompt),
                                                  tool_use_agent_id)
            print(response.content)

       # Print the environment variables after injection
        print("New environment keys after injection:")
        new_keys = set(os.environ.keys()) - set(before_os_dict.keys())

    except Exception as e:
        print(f'An error occurred: {e.args[0]}')
    finally:
        try:
            # Stop processing messages.
            await runtime.stop()
        except Exception as e:
            print(f'An error occurred during cleanup: {e.args[0]}')


if __name__ == '__main__':
    asyncio.run(main())
