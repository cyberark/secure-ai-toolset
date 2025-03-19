# Autogen Example

This directory contains examples demonstrating how to populate environment variables automatically.
In both examples below, we use AWS Secrets Manager as an example secret provider to store environment variables.

Example 1 uses a decorator to populate and depopulate environment variables.
```python

@EnvironmentVariablesManager.set_env_vars(AWSSecretsProvider())
async def main() -> None:
    
    # agent does something - environment variables are automatically populated and depopulated

```

Example 2 uses a 'with' statement to populate and depopulate environment variables.
```python
 with EnvironmentVariablesManager(AWSSecretsProvider()):   
    runtime.start()

    # Send a direct message to the tool agent.
    prompt = f"What is the stock price of NVDA on 2024/06/01? "
    tool_use_agent_id = AgentId(type="tool_use_agent", key="2")
    response = await runtime.send_message(Message(prompt),
                                            tool_use_agent_id)
````

Environment variables are stored in the secret provider, loaded into memory, and wiped after usage.

In these scripts, a SingleThreadedAgentRuntime is used to create and register Tools (such as fetching stock prices), 
and messages are processed by agents within a secure environment where variables are automatically loaded and removed.


