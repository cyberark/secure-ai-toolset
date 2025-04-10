# Getting started with the credentials module

## Add the dependencies

This module is available on PyPI. Add agent-guard-core to your project:

### uv
```bash
uv add agent-guard-core
```

### pip
```bash
pip3 install agent-guard-core
```


### poetry
```bash
poetry add agent-guard-core
```

**_NOTE:_** Please ensure you are using Poetry version >=2.1.1.

## Choose a provider

Choose the provider with which you want to manage your environment variables.  
The `namespace` parameter determines the location of the secret/file in which the variables are stored.   

**_NOTE:_** You can also combine providers. For example, use the local file provider for non-sensitive environment variables and then a secret manager for the sensitive variables.

### Local file (for development purposes, or non-sensitive data)

Get environment variables from a local `.env` file.  
You can use a different file name, using the `namespace` parameter.

#### Setup

Create a local `.env` file in your project directory. This file should contain the environment variables you want to set.

Example:

```dotenv
MY_ENVIRONMENT_VARIABLE_NAME="..."
```

#### Usage

Example using a `with` statement:

```python
  with EnvironmentVariablesManager(FileSecretsProvider()):
    # environment variables will be available only in this section
    ...
    my agentic code
    ...
```

### AWS Secrets Manager

Get environment variables from a secret stored in AWS Secrets Manager.  
The secret name is determined by the `namespace` parameter as follows: `<namespace>/agentic_env_vars`

#### Setup

Make sure you have a valid AWS credentials configured. You can set them up using the AWS CLI or by setting the following environment variables. For example:

```shell
aws sso login --profile my-profile
```

#### Usage

Example using a `with` statement:

```python
  with EnvironmentVariablesManager(AWSSecretsProvider(namespace='my-prefix')):
    # environment variables will be available only in this section
    ...
    my agentic code
    ...
```

### CyberArk Conjur

Get environment variables from a secret stored in [CyberArk Conjur](https://www.conjur.org/).  
The secret name is determined by the `namespace` parameter as follows: `<namespace>/agentic_env_vars`

#### Setup

The Conjur provider supports the following environment variables:

| Environment Variable    | Description                                                                               | Required?                                  |
|-------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------|
| CONJUR_APPLIANCE_URL    | The Conjur base URL. For example, "https://my-org.secretsmgr.cyberark.cloud/api"          | Yes                                        |
| CONJUR_AUTHN_LOGIN      | The Conjur host (workload ID) with which the login to Conjur will be made                 | Yes                                        |
| CONJUR_AUTHN_API_KEY    | The API key of the Conjur host (workload ID) to authenticate to Conjur                    | Yes, if API key authentication is used     |
| CONJUR_AUTHENTICATOR_ID | If an API key is not used, which authenticator should be used to authenticate to Conjur   | Yes, if API key authentication is not used |
| CONJUR_ACCOUNT          | The Conjur account. Default: "conjur"                                                     | No                                         |
| CONJUR_AUTHN_IAM_REGION | If using an IAM authenticator, which AWS region should be accessed. Default: "us-east-1"  | No                                         |

Define the environment variables for your program, based on the way you want to authenticate to Conjur.

Example when authenticating to Conjur using an API key:

```shell
export CONJUR_APPLIANCE_URL="https://my-org.secretsmgr.cyberark.cloud/api"
export CONJUR_AUTHN_LOGIN="<your workload ID>"
export CONJUR_AUTHN_API_KEY="<API key>"
```

Example when authenticating to Conjur using the AWS IAM authenticator:

```shell
export CONJUR_APPLIANCE_URL="https://my-org.secretsmgr.cyberark.cloud/api"
export CONJUR_AUTHN_LOGIN="<your workload ID>"
export CONJUR_AUTHENTICATOR_ID="authn-iam/default"
```

Create the secret that will contain the environment variables.

Save the following yaml file into `data.yml`:

```yaml
- !policy
  id: my-app-policy
  owner: !host my-workload
  body:
    - !variable agentic_env_vars
```

Load `data.yml`:

```shell
conjur policy load -b data -f data.yml
```

Then, store the environment variables in the secret:

```shell
conjur variable set -i data/my-app-policy/agentic_env_vars -v '{"MY_ENVIRONMENT_VARIABLE_NAME": "...", "MY_OTHER_ENVIRONMENT_VARIABLE_NAME": "..." }'
```

#### Usage

Example using a `with` statement:

```python
  with EnvironmentVariablesManager(ConjurSecretsProvider(namespace="data/my-app-policy")):
    # environment variables will be available only in this section
    ...
    my agentic code
    ...
```
