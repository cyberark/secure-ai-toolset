# Credentials Module

The `credentials` module simplifies managing sensitive information like API keys and secrets. It provides a unified interface for secure storage, retrieval, and management, supporting multiple secret providers and extensibility for custom implementations.

## Features
- **Environment Variables Provisioning** just-in-time provisioning of API keys and other environment variables. The environment variables will be populated in a specific section and wiped right after.

Sample using a `with` statement:
```python
  with EnvironmentVariablesManager(AWSSecretsProvider()):
    # environment variables as API Keys will be available only in this section
    ...
    my agentic code
    ...
```

Sample using a `decorator`:
```python
  @EnvironmentVariablesManager.set_env_vars(ConjurSecretsProvider())
  def my_agentic_function():
    ...
    my agentic code
    ...
```

Sample using direct function call:
```python
  def my_agentic_function2():
    env_manager = EnvironmentVariablesManager(
        FileSecretsProvider())
    env_manager.populate_env_vars()

    ...
    my agentic code
    ...

    env_manager.depopulate_env_vars()
```

- **Secure Secret Management**: Retrieve and store secrets securely using supported providers with a code example below:

```python
from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider

# Initialize the provider
provider = AWSSecretsProvider()

# Store a secret
provider.store("my_secret_key", "my_secret_value")

# Retrieve a secret
secret_value = provider.get("my_secret_key")

# Delete a secret
provider.delete("my_secret_key")
```
- **Supported Providers**
    - **CyberArk Conjur**: Integrate with CyberArk's Conjur for enterprise-grade secret management.
    - **AWS Secrets Manager**: Securely manage secrets in AWS.
    - **Google Cloud Secret Manager**: Securely manage secrets in GCP.
    - **Local .env Files**: Use .env files for development and testing purposes.

- **Extensible**: Implement custom secret providers by extending the `SecretsProvider` interface.

## Extensibility and Contributing
The module is extensible. Add support for new secret management systems by implementing the `SecretsProvider` interface. For contributions, refer to the [CONTRIBUTING](../../CONTRIBUTING.md) file.

To implement a custom provider, extend the `SecretsProvider` interface and implement its methods:

```python
class MyCustomSecretsProvider(SecretsProvider):
    def connect(self):
        # Custom connection logic
        pass

    def store(self, key, value):
        # Custom logic to store a secret
        pass

    def get(self, key):
        # Custom logic to retrieve a secret
        pass

    def delete(self, key):
        # Custom logic to delete a secret
        pass
```

## License
This module is licensed under the Apache License 2.0. See the [LICENSE](../../LICENSE) file for details.