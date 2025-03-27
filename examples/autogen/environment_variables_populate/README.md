# Autogen Examples

This directory contains examples demonstrating how to populate environment variables automatically.
In both examples below, we use AWS Secrets Manager as a secret provider to store environment variables, and we use Azure OpenAI as the LLM.
The examples assume that there is a secret stored in AWS Secrets Manager, named `default/agentic_env_vars` with a JSON object containing the following key-value pairs:

```json
{
  "AZURE_OPENAI_ENDPOINT": "<your-azure-openai-endpoint>",
  "AZURE_OPENAI_KEY": "<your-azure-openai-key>"
}
```

## Example 1

This example uses a decorator to populate and depopulate environment variables in the scope it's being used. 

```python

@EnvironmentVariablesManager.set_env_vars(AWSSecretsProvider())
async def main() -> None:
    
    # Agents perform their tasks - environment variables are automatically populated and depopulated

```

## Example 2

Uses a 'with' statement to populate and depopulate environment variables.

```python
with EnvironmentVariablesManager(AWSSecretsProvider()):   
    runtime.start()
    
    # Send a direct message to the tool agent.
    prompt = f"What is the stock price of NVDA on 2024/06/01? "
    tool_use_agent_id = AgentId(type="tool_use_agent", key="2")
    response = await runtime.send_message(Message(prompt), tool_use_agent_id)
```

Environment variables are stored in the secret provider, loaded into memory, and wiped after usage.

In these scripts, a SingleThreadedAgentRuntime is used to create and register Tools (such as fetching stock prices), 
and messages are processed by agents within a secure environment where variables are automatically loaded and removed.