# AI Security Toolset - A toolset repository for AI agents

## Overview

This toolset is intended for AI agents builders, to simplify your work, and reduce the level of boilerplate code you need to write.

## Features

### Secured environment variables provisioning 

This toolset can populate API keys and secrets as environment variables. The secrets are stored in your secret management of choice and are provisioned at runtime into your process memory.  
The secrets can be populated and depopulated, for a specific context: Agent, Tool, HTTP call.  

Currently [supported](secure_ai_toolset/secrets) secret providers:

- AWS Secret Manager
- CyberArk Conjur
- Local `.env` file (for development purposes)

However, this functionality is extensible, by implementing a [SecretsProvider](secure_ai_toolset/secrets/secrets_provider.py) interface.

#### Example

For full, runnable examples, please see the [examples](examples) directory.

```python
...

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
                api_version='2024-02-01',
                api_key=os.getenv('AZURE_OPENAI_KEY')),
            [tool.schema for tool in tools], 'tool_executor_agent'),
    )

    ...
```

## Getting Started

1. Consume the toolset from [pypi](https://test.pypi.org/project/secure-ai-toolset/).
2. Follow one of our [examples](examples) to see how to use the toolset.

### pip

```bash
pip3 install secure-ai-toolset
```

### poetry

```bash
poetry add secure-ai-toolset
```

**Note:** Please ensure you are using Poetry version >=2.1.1.

## Contribution

Please make sure to read the [CONTRIBUTING.md](CONTRIBUTING.md) file if you want to contribute to this project.

## Contact
Feel free to contact us via github issues. If there are any feature requests or issues in the project you may contact me through linkedin: [Gil Adda](https://www.linkedin.com/in/gil-adda-6117b9/) 
