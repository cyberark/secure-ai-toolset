# secure-ai-toolset

A toolset repository for AI agents.

## Overview

A toolset for AI builders to use in agentic AI frameworks to secure API keys, provide authentication, and authorization.

## Features

### Secured environment variables provisioning 
This toolset can populate API keys as environment variables. The API keys are stored at the following secret providers and provisioned to the process memory only. These are the supported secret providers:
* AWS Secret Manager
* CyberArk Conjur
The secrets can be populated and depopulated, for a specific context: Agent, Tool, HTTP call
Secrets are organized in namespaces, to limit teh exposure to minimum

### OAuth token validation 

TBD

### Authorization to tool calls

TBD

### Auditing of calls

TBD


## Installation

To download the toolset, use the following command:

```sh
git clone https://github.com/your-repo/secure-ai-toolset.git
```

## Setup instructions

### pip
```bash
pip3 install secure-ai-toolset
```

### poetry
> **Note:** Ensure you have Poetry version greater than 1.8.0 installed.

```bash
poetry add secure-ai-toolset
```


## Usage

Here is an example of how to consume the toolset in your project:

```python
# Import the necessary modules from the toolset
from secure_ai_toolset import APIKeyManager, AuthManager

# Initialize the API key manager
api_key_manager = APIKeyManager()
api_key_manager.secure_key('your-api-key')

# Initialize the authentication manager
auth_manager = AuthManager()
auth_manager.authenticate_user('username', 'password')
```

For more detailed documentation, please refer to the [docs](docs/README.md).

