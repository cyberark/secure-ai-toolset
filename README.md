<p style="text-align: center;">
    <img src="https://raw.githubusercontent.com/cyberark/agent-guard/refs/heads/main/resources/logo.png" alt="agentwatch - AI Agent Observability Platform" width="400"/>
    
</p>
<h3 style="font-family: 'Fira Mono', Monospace; text-align: center;">Security Toolset for AI Agents</h3>

<p style="text-align: center;">
    <a href="https://github.com/cyberark/agent-guard/commits/main">
        <img alt="GitHub last commit" src="https://img.shields.io/github/last-commit/cyberark/agent-guard">
    </a>
    <a href="https://github.com/cyberark/agent-guard">
        <img alt="GitHub code size" src="https://img.shields.io/github/languages/code-size/cyberark/agent-guard">
    </a>
    <a href="https://github.com/cyberark/agent-guard/blob/main/LICENSE">
        <img alt="GitHub License" src="https://img.shields.io/github/license/cyberark/agent-guard"/>
    </a>
    <a href="https://pypi.org/project/agent-guard-core">
        <img alt="PYPI version" src="https://img.shields.io/pypi/v/agent-guard-core" />
    </a>   
</p>


## 🌟 Overview

This toolset is intended for AI agent builders to simplify your work and reduce the level of boilerplate code you need to write.
The toolset includes a [Python library](https://pypi.org/project/agent-guard-core/).


## Key Features

### ✨ Secured environment variables provisioning

This toolset can populate API keys and secrets as environment variables. The secrets are stored in your secret management of choice and are provisioned at runtime into your process memory.
The secrets can be populated and depopulated, for a specific context: Agent, Tool, HTTP call.
Currently [supported](https://github.com/cyberark/agent-guard/tree/main/agent_guard_core/credentials) secret providers:
- CyberArk Conjur
- AWS Secrets Manager
- Local `.env` file (for development purposes)

However, this functionality is extensible by implementing a [SecretsProvider](https://github.com/cyberark/agent-guard/tree/main/agent_guard_core/credentials) interface.

#### Example

For full, runnable examples, please see the [examples](https://github.com/cyberark/agent-guard/tree/main/examples) directory.

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

Please take a look at our [getting started](https://github.com/cyberark/agent-guard/blob/main/GETTING_STARTED.md) page and try it out!

## 🤝 Contribution

Please make sure to read the [CONTRIBUTING.md](https://github.com/cyberark/agent-guard/blob/main/CONTRIBUTING.md) file if you want to contribute to this project.

## 💁  Contact

Feel free to contact us via GitHub issues or through LinkedIn: [Gil Adda](https://www.linkedin.com/in/gil-adda-6117b9/), [Rafi Schwarz](https://www.linkedin.com/in/rafi-schwarz/). 
