# Credentials Module

The `credentials` module simplifies managing sensitive information like API keys and secrets. It provides a unified interface for secure storage, retrieval, and management, supporting multiple secret providers and extensibility for custom implementations.

## Features
- **Environment Variables Provisioning**: Just-in-time provisioning of API keys and other environment variables. The environment variables will be populated in a specific section and wiped right after.
A sample usage looks like:
```python
  with EnvironmentVariablesManager(AWSSecretsProvider()):
    # Environment variables such as API keys will be available only in this section

    ...
    my agentic code
    ...
```
- **Secure Secret Management**: Retrieve and store secrets securely using supported providers with a code example below.
We protect sensitive data through the following measures:
* OS environment variables are securely stored in a secret store, instead of in the operating system.
* Environment variables are loaded into the application environment just-in-time (JIT) for usage and immediately cleared after their intended use, significantly reducing the potential attack surface.
* Python memory references to secrets are cleared promptly by explicitly invoking the garbage collector.

Important Caveat: Python strings are immutable, which means they cannot be altered once created. Therefore, sensitive information may still be exposed if the process memory is captured or dumped.

```python
from agent_guard_core.credentials.aws_secrets_manager_provider import AWSSecretsProvider

# Initialize the provider
provider = AWSSecretsProvider()

# Store a secret
provider.store("my_secret_key", "my_secret_value")

# Retrieve a secret
secret_value = provider.get("my_secret_key")
print(f"Retrieved secret: {secret_value}")

# Delete a secret
provider.delete("my_secret_key")
```
- **Supported Providers**
    - **AWS Secrets Manager**: Securely manage secrets in AWS.
    - **CyberArk Conjur**: Integrate with CyberArk's Conjur for enterprise-grade secret management.
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

    def get_secret_dictionary(self) -> Dict[str, str]:
        # Custom logic to get secret dictionary
        pass

    def store_secret_dictionary(self, secret_dictionary: Dict):
        # Custom logic to store secret dictionary
        pass

```

## License
This module is licensed under the Apache License 2.0. See the [LICENSE](../../LICENSE) file for details.