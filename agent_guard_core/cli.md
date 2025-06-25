# Agent Guard CLI

The Agent Guard CLI provides commands to configure and manage secret providers and MCP proxy capabilities.

## Usage

```sh
agc [COMMAND] [OPTIONS]
```

## Commands

### **mcp-proxy**

Group of commands to manage Agent Guard MCP proxy.

- #### **start**

  Starts the Agent Guard MCP proxy.

  **Options:**
  - `--debug, -d`  
    Enable debug mode for verbose logging.
  - `--cap, -c [CAPABILITY]`  
    Enable specific capabilities for the MCP proxy.  
    Choices: `audit`  
    Can be specified multiple times for multiple capabilities.
  - `ARGV`  
    Command and arguments to start an MCP server.

  **Examples:**
  ```sh
  # Start MCP proxy with audit logging for a specific MCP server
  agc mcp-proxy start --cap audit uvx mcp-server-fetch

  # Start with debug logging
  agc mcp-proxy start -d --cap audit uvx mcp-server-fetch
  
  # For containerized environments with persistent logs
  docker run -v /path/to/local/logs:/logs agc mcp-proxy start --cap audit uvx mcp-server-fetch
  ```

- #### **apply-config**

  Apply MCP proxy configuration to an existing MCP configuration file.

  **Options:**
  - `--mcp-config-file, -cf [FILE]`  
    Path to the MCP configuration file. Default: Auto-detect under /config/*.json.
  - `--cap, -c [CAPABILITY]`  
    Enable specific capabilities for the MCP proxy.  
    Choices: `audit`

  **Example:**
  ```sh
  # For local use
  agc mcp-proxy apply-config --mcp-config-file config_example.json --cap audit

  # For containerized environments
  docker run -v /path/to/local/config:/config agc mcp-proxy apply-config --cap audit
  ```

  **Note:** When using containerized environments, mount your local config directory to the `/config` folder in the container using the `-v` flag (e.g., `-v /path/to/local/config:/config`). The command will automatically detect JSON configuration files in the mounted directory.

- #### **Capabilities**

  Agent Guard MCP Proxy supports the following capabilities that can be enabled with the `--cap` option:

  ##### Audit Logging

  When the `audit` capability is enabled (`--cap audit`), the proxy logs all MCP operations to a file:

  - `/logs/agent_guard_core_proxy.log` if `/logs` is writable
  - `agent_guard_core_proxy.log` in the current directory otherwise

  These logs include detailed information about each request and response, including:
  - The operation type (ListTools, CallTool, ListPrompts, etc.)
  - Full request parameters
  - Complete response data

  This provides a comprehensive audit trail suitable for security monitoring and compliance.

  **Important Security Note:** Audit logs may contain sensitive information from both requests and responses, including any data submitted to or returned from the AI model. Ensure logs are stored securely with appropriate access controls, and implement log rotation and retention policies according to your organization's security requirements.

  **Note for containerized environments:** To persist audit logs from containers, mount a local directory to the container's `/logs` directory:
  ```sh
  docker run -v /path/to/local/logs:/logs agc mcp-proxy start --cap audit <command>
  ```
  
  This ensures logs are preserved even after the container exits.

- #### **Integration with Claude Desktop / Amazon Q CLI**

  You can configure Claude Desktop / Amazon Q CLI to use the Agent Guard MCP Proxy by creating a configuration file:

  ```json
  {
    "mcpServers": {
      "agc_proxy": {
        "command": "agc",
        "args": [
          "mcp-proxy",
          "start",
          "--cap",
          "audit",
          "uvx",
          "mcp-server-fetch"
        ]
      }
    }
  }
  ```

### **secrets**

Group of commands to manage secrets.

- #### **set**

  Store a secret in the configured secret provider.

  **Options:**
  - `--provider, -p [PROVIDER]`  
    The secret provider to store the secret.
  - `--secret_key, -k [KEY]`  
    The name of the secret to store.
  - `--secret_value, -v [VALUE]`  
    The value of the secret to store.
  - `--namespace, -n [NAMESPACE]`  
    (Optional) The namespace to organize secrets. Default: `default`.
  - Various provider-specific options for AWS, GCP, and Conjur.

  **Example:**
  ```sh
  # Store a secret in the default namespace
  agc secrets set -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret -v "my-secret-value"
  
  # Store a secret in a custom namespace
  agc secrets set -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret -v "my-secret-value" -n production
  ```

  **Note:** Secrets are organized within namespaces. In AWS Secrets Manager, for example, secrets are stored as key-value pairs within a single JSON object located at `{namespace}/agentic_env_vars` (e.g., `default/agentic_env_vars` or `production/agentic_env_vars`).

- #### **get**

  Retrieve a secret from the configured secret provider.

  **Options:**
  - `--provider, -p [PROVIDER]`  
    The secret provider to retrieve the secret from.
  - `--secret_key, -k [KEY]`  
    The name of the secret to retrieve.
  - `--namespace, -n [NAMESPACE]`  
    (Optional) The namespace to retrieve the secret from. Default: `default`.
  - Various provider-specific options for AWS, GCP, and Conjur.

  **Example:**
  ```sh
  # Retrieve a secret from the default namespace
  agc secrets get -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret
  
  # Retrieve a secret from a custom namespace
  agc secrets get -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret -n production
  ```


  **Note:** When retrieving secrets, you must specify the same namespace used when storing the secret.

### **configure**

Group of commands to manage Agent Guard configuration.

**Note:** The configure commands are not relevant for containerized environments, as configuration in containers is typically managed through environment variables or mounted config files.

- #### **set**

  Set the secret provider and related configuration options.

  **Options:**
  - `--provider [PROVIDER]`  
    The secret provider to store and retrieve secrets.  
    Choices: `AWS_SECRETS_MANAGER_PROVIDER`, `FILE_SECRET_PROVIDER`, `CONJUR_SECRET_PROVIDER`, `GCP_SECRETS_MANAGER_PROVIDER`  
    Default: `FILE_SECRET_PROVIDER`

  - `--conjur-authn-login [LOGIN]`  
    (Optional) Conjur authentication login (workload ID).

  - `--conjur-appliance-url [URL]`  
    (Optional) Endpoint URL of Conjur Cloud.

  - `--conjur-authenticator-id [ID]`  
    (Optional) Conjur authenticator ID.

  - `--conjur-account [ACCOUNT]`  
    (Optional) Conjur account ID.

  - `--conjur-api-key [KEY]`  
    (Optional) Conjur API key.

  - `--aws-region [REGION]`  
    (Optional) AWS region.

  - `--aws-access-key-id [KEY]`  
    (Optional) AWS access key ID.

  - `--aws-secret-access-key [KEY]`  
    (Optional) AWS secret access key.

  - `--gcp-project-id [ID]`  
    (Optional) GCP project ID.

  - `--gcp-secret-id [ID]`  
    (Optional) GCP secret ID.

  - `--gcp-region [REGION]`  
    (Optional) GCP region.

  - `--gcp-replication-type [TYPE]`  
    (Optional) GCP replication type: automatic or user-managed.

  **Example:**
  ```sh
  agc config set --provider CONJUR_SECRET_PROVIDER --conjur-authn-login my-app --conjur-api-key my-key --conjur-appliance-url https://conjur.example.com
  ```

- #### **list**

  List all configuration parameters and their values.

  **Example:**
  ```sh
  agc config list
  ```

- #### **get**

  Get the value of a specific configuration parameter.

  **Options:**
  - `--key [KEY]`  
    Configuration key to retrieve.

  **Example:**
  ```sh
  agc config get --key SECRET_PROVIDER
  ```

## Help

For help on any command, use the `--help` flag:

```sh
agc mcp-proxy start --help
```

---

**Note:**  
The CLI stores configuration in a file under your home directory: `~/.agent_guard/config.env`
