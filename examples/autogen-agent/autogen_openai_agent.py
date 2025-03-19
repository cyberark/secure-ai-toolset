import asyncio
import os
import random
from dataclasses import dataclass
from typing import Annotated, List

from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from autogen_core.models import ChatCompletionClient, LLMMessage, SystemMessage, UserMessage
from autogen_core.tool_agent import ToolAgent, tool_agent_caller_loop
from autogen_core.tools import FunctionTool, Tool, ToolSchema
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.environment_manager import EnvironmentVariablesManager


@dataclass
class Message:
    content: str


async def get_stock_price(ticker: str,
                          date: Annotated[str, 'Date in YYYY/MM/DD']) -> float:
    """
    Get the stock price for a given ticker and date.

    Args:
        ticker (str): The stock ticker symbol.
        date (str): The date in YYYY/MM/DD format.

    Returns:
        float: The stock price.
    """
    # Check if the ticker is valid
    if not ticker.isalpha():
        raise ValueError(f"Invalid ticker symbol: {ticker}")
    # Returns a random stock price for demonstration purposes.
    return random.uniform(10, 200)


class ToolUseAgent(RoutedAgent):
    """
    An agent that uses tools to process messages.
    """

    def __init__(self, model_client: ChatCompletionClient,
                 tool_schema: List[ToolSchema], tool_agent_type: str) -> None:
        """
        Initialize the ToolUseAgent.

        Args:
            model_client (ChatCompletionClient): The model client for chat completion.
            tool_schema (List[ToolSchema]): The schema of tools available to the agent.
            tool_agent_type (str): The type of tool agent.
        """
        super().__init__('An agent with tools')
        self._system_messages: List[LLMMessage] = [
            SystemMessage(content='You are a helpful AI assistant.')
        ]
        self._model_client = model_client
        self._tool_schema = tool_schema
        self._tool_agent_id = AgentId(tool_agent_type, self.id.key)

    @message_handler
    async def handle_user_message(self, message: Message,
                                  ctx: MessageContext) -> Message:
        """
        Handle a user message and return a response.

        Args:
            message (Message): The user message.
            ctx (MessageContext): The message context.

        Returns:
            Message: The response message.
        """
        # Create a session of messages.
        session: List[LLMMessage] = [
            UserMessage(content=message.content, source='user')
        ]

        # Run the caller loop to handle tool calls.
        messages = await tool_agent_caller_loop(
            self,
            tool_agent_id=self._tool_agent_id,
            model_client=self._model_client,
            input_messages=session,
            tool_schema=self._tool_schema,
            cancellation_token=ctx.cancellation_token,
        )
        # Return the final response.
        assert isinstance(messages[-1].content, str)

        return Message(content=messages[-1].content)


@EnvironmentVariablesManager.set_env_vars(AWSSecretsProvider())
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
                azure_endpoint='https://rafi-test-openai.openai.azure.com',
                azure_deployment='gpt-4o',
                api_version='2024-02-01',
                api_key=os.getenv('AZURE_OPENAI_KEY')),
            [tool.schema for tool in tools], 'tool_executor_agent'),
    )

    try:
        # unsafe load the secrets from environment variables..
        # from dotenv import load_dotenv
        # load_dotenv()

        # safe load the secrets from a secret provider
        # env_var_mgr = EnvironmentVariablesManager(
        #     secret_provider=AWSSecretsProvider(region_name="us-east-1"))
        # env_var_mgr.populate_env_vars()

        # Start processing messages.
        runtime.start()

        # Send a direct message to the tool agent.
        prompt = f"What is the stock price of NVDA on 2024/06/01? "
        tool_use_agent_id = AgentId(type="tool_use_agent", key="2")
        response = await runtime.send_message(Message(prompt),
                                              tool_use_agent_id)
        print(response.content)

        # wipe out the secrets after usage
        # env_var_mgr.depopulate_env_vars()

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
