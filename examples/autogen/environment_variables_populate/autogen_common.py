import random
from dataclasses import dataclass
from typing import Annotated, List

from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from autogen_core.models import ChatCompletionClient, LLMMessage, SystemMessage, UserMessage
from autogen_core.tool_agent import tool_agent_caller_loop
from autogen_core.tools import ToolSchema


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
