# Credentials Module

The `credentials` module simplifies managing sensitive information like API keys and secrets. It provides a unified interface for secure storage, retrieval, and management, supporting multiple secret providers and extensibility for custom implementations.

## Features
- **Environment Variables Provisioning** just-in-time provisioning of API keys and other environment variables. The environment variables will be populated in a specific section and wiped right after.
A sample usage looks like:
```python
  with EnvironmentVariablesManager(AWSSecretsProvider()):
    # environment variables as API Keys will be available only in this section

    ...
    my agentic code
    ...
```
- **Secure Secret Management**: Retrieve and store secrets securely using supported providers with a code example below:

```python
from secure_ai_toolset.credentials.aws_secrets_manager_provider import AWSSecretsProvider

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


## Components

### 1. `EnvironmentVariablesManager`
A utility for just-in-time provisioning of environment variables. It ensures that sensitive information like API keys is available only within a specific code block and is wiped immediately after.

### 2. `AWSSecretsProvider`
A provider implementation for AWS Secrets Manager. It allows secure retrieval and storage of secrets in AWS.

### 3. `SecretsProvider`
An interface that defines the contract for implementing custom secret providers. Any new provider must implement this interface.

### 4. `SecretProviderException`
A custom exception class used to handle errors related to secret management.


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