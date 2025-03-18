import asyncio
import os
import random
import uuid
from dataclasses import dataclass
from typing import Annotated, List

from autogen_core import MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler
from autogen_core.models import ChatCompletionClient, LLMMessage, SystemMessage, UserMessage
from autogen_core.tool_agent import ToolAgent, tool_agent_caller_loop
from autogen_core.tools import FunctionTool, Tool, ToolSchema
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient


@dataclass
class Message:
    content: str


async def get_stock_price(ticker: str,
                          date: Annotated[str, 'Date in YYYY/MM/DD']) -> float:
    # Check if the ticker is valid
    if not ticker.isalpha():
        raise ValueError(f"Invalid ticker symbol: {ticker}")
    # Returns a random stock price for demonstration purposes.
    return random.uniform(10, 200)


class ToolUseAgent(RoutedAgent):

    def __init__(self, model_client: ChatCompletionClient,
                 tool_schema: List[ToolSchema], tool_agent_type: str) -> None:
        super().__init__('An agent with tools')
        self._system_messages: List[LLMMessage] = [
            SystemMessage(content='You are a helpful AI assistant.')
        ]
        self._model_client = model_client
        self._tool_schema = tool_schema
        self._tool_agent_id = uuid.uuid4()

    @message_handler
    async def handle_user_message(self, message: Message,
                                  ctx: MessageContext) -> Message:
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

    @staticmethod
    def factory(model_client: ChatCompletionClient,
                tool_schema: List[ToolSchema], tool_agent_type: str):
        model_client = model_client,
        agent = ToolUseAgent(model_client=model_client,
                             tool_schema=tool_schema,
                             tool_agent_type=tool_agent_type)
        agent._id = uuid.uuid4()
        return agent


async def main() -> None:

    # Create a runtime.
    runtime = SingleThreadedAgentRuntime()

    ## populate with secrets

    # Define the tools to be used by the agent
    tools: List[Tool] = [ FunctionTool(get_stock_price, description='Get the stock price.')   ]

    # Define the agent creation factory
    def executor_factory():
        tool_agent_type = 'tool_executor_agent'
        agent = ToolAgent(description=tool_agent_type, tools=tools)
        return agent

    # register the agent in the runtime
    await ToolAgent.register(runtime, 'tool_executor_agent', executor_factory)

    def tool_use_agent_factory():
        api_key = os.getenv('AZURE_OPENAI_KEY')
        agent = ToolUseAgent(
            AzureOpenAIChatCompletionClient(
                model='gpt-4o',
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                azure_deployment='gpt-4o',
                api_version='2024-02-01',
                api_key=api_key), [tool.schema for tool in tools],
            'tool_executor_agent')
        return agent

    await ToolUseAgent.register(runtime, 'tool_use_agent', tool_use_agent_factory)

    try:
        # Start processing messages.
        runtime.start()

        # Send a direct message to the tool agent.
        prompt = f"What is the stock price of NVDA on 2024/06/01? "
        tool_use_agent_id = uuid.uuid4()
        response = await runtime.send_message(Message(prompt), tool_use_agent_id)
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
