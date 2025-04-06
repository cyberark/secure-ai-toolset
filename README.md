<p align="center">
    <img src="resources/logo.png" alt="agentwatch - AI Agent Observability Platform" width="400"/>
</p>
<h3 align="center" style="font-family: 'Fira Mono', Monospace;">Security Toolset for AI Agents</h3>

<p align="center">
    <a href="https://github.com/cyberark/agent-guard/commits/main">
        <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/cyberark/agent-guard">
    </a>
    <a href="https://github.com/cyberark/agent-guard">
        <img alt="GitHub code size" src="https://img.shields.io/github/languages/code-size/cyberark/agent-guard">
    </a>
    <a href="https://github.com/cyberark/agent-guard/blob/main/LICENSE">
        <img alt="GitHub License" src="https://img.shields.io/github/license/Cyberark/agent-guard" />
    </a>
</p>


## 🌟 Overview

This toolset is intended for AI agents builders, to simplify your work, and reduce the level of boilerplate code you need to write.
The toolset includes a [Python library](https://pypi.org/project/agent-guard-core/).



## Key Features

### ✨ Secured environment variables provisioning

This toolset can populate API keys and secrets as environment variables. The secrets are stored in your secret management of choice and are provisioned at runtime into your process memory.
The secrets can be populated and depopulated, for a specific context: Agent, Tool, HTTP call.
Currently [supported](secure_ai_toolset/cerdentials) secret providers:
- AWS Secret Manager
- CyberArk Conjur
- Local `.env` file (for development purposes)
However, this functionality is extensible, by implementing a [SecretsProvider](agent_gaurd_core/credentials/secrets_provider.py) interface.

#### Example

For full, runnable examples, please see the [examples](examples) directory.

```python
...

from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider
from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager


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

    ...
```

## ⚡ Getting Started

1. Consume the toolset from [pypi](https://test.pypi.org/project/agent-guard-core/).
2. Follow one of our [examples](examples) to see how to use the toolset.

### pip

```bash
pip3 install agent-guard-core
```

### poetry

```bash
poetry add agent-guard-core
```

**Note:** Please ensure you are using Poetry version >=2.1.1.

## 🤝 Contribution

Please make sure to read the [CONTRIBUTING.md](CONTRIBUTING.md) file if you want to contribute to this project.

## 💁  Contact

Feel free to contact us via GitHub issues or through LinkedIn: [Gil Adda](https://www.linkedin.com/in/gil-adda-6117b9/), [Rafi Schwarz](https://www.linkedin.com/in/rafi-schwarz/). 
