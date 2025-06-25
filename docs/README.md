# Integration Tests

## Conjur Provider Test

The Conjur provider supports the following environment variables:

| Environment Variable    | Description                                                                               | Required?                                  |
|-------------------------|-------------------------------------------------------------------------------------------|--------------------------------------------|
| CONJUR_APPLIANCE_URL    | The Conjur base URL. For example, "https://my-org.secretsmgr.cyberark.cloud/api"          | Yes                                        |
| CONJUR_AUTHN_LOGIN      | The Conjur host (workload ID) with which the login to Conjur will be made                 | Yes                                        |
| CONJUR_AUTHN_API_KEY    | The API key of the Conjur host (workload ID) to authenticate to Conjur                    | Yes, if API key authentication is used     |
| CONJUR_AUTHENTICATOR_ID | If an API key is not used, which authenticator should be used to authenticate to Conjur   | Yes, if API key authentication is not used |
| CONJUR_ACCOUNT          | The Conjur account. Default: "conjur"                                                     | No                                         |
| CONJUR_AUTHN_IAM_REGION | If using an IAM authenticator, which AWS region should be accessed. Default: "us-east-1"  | No                                         |

### Running the Conjur Provider Test

To run the Conjur provider, follow the steps blow:

Create a file called `data.yml` with the following content:

```yaml
- !host
  id: my-workload
  annotations:
    authn/api-key: true

- !policy
  id: test-toolset
  owner: !host my-workload
  body: []
```

Load the policy to Conjur:

```shell
conjur policy load -b data -f data.yml
```

Then export the environment variables as described in the table above.

Example:
```shell
export CONJUR_APPLIANCE_URL="https://my-org.secretsmgr.cyberark.cloud/api"
export CONJUR_AUTHN_LOGIN="host/data/my-workload"
export CONJUR_AUTHN_API_KEY="<API key>"
```

Then execute the following command to run the tests:

```sh
pytest -v -m conjur ./tests/integration
```

## AWS Secrets Manager Provider Test

### Running the AWS Secrets Manager provider tests

Ensure that you:

- Have an AWS Account
- An IAM role with CRUD permissions for AWS Secrets Manager
- Valid AWS session (via AWS CLI / EC2 instance etc..)

Then run the tests using the following command:

```bash
pytest -v -m aws ./tests/integration
```