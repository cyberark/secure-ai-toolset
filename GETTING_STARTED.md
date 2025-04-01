# Getting started with a new project
## Set up a new project
To set up this example, create a new project and install the dependencies. 
The instructions are given for Poetry and can be modified for other package managers.

To create a new project called 'test-secure-ai' run these commands:
```bash
poetry new test-secure-ai
cd test-secure-ai
poetry env activate
```

Add the project library and autogen dependencies:
```bash
poetry add secure-ai-toolset
poetry add autogen-core
poetry add "autogen-ext[openai]"
```

# Copy the following example to your project

Copy the code below to your python main program. e.g main.py

```python
# ...existing code...

from secure_ai_toolset.secrets.aws_secrets_manager_provider import AWSSecretsProvider
from secure_ai_toolset.secrets.environment_manager import EnvironmentVariablesManager


# Populate the environment variables from AWS Secrets Manager
@EnvironmentVariablesManager.set_env_vars(AWSSecretsProvider())
async def main() -> None:
    runtime = SingleThreadedAgentRuntime()
    tools: List[Tool] = [
        FunctionTool(get_stock_price, description='Get the stock price.')
    ]
    
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
                api_version='2024-02-01'),
            [tool.schema for tool in tools], 'tool_executor_agent'),
    )

    # ...existing code...
```
# Setup Environment File cre

seup your local machine with AWS credentials or use another 

# Run the example  

run the code you copied to your python

```bash
python main,py
```
