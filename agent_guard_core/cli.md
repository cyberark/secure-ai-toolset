# Agent Guard CLI

The Agent Guard CLI provides commands to manage secret providers and MCP proxy capabilities.

## Usage

```
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
  - `--secret-uri, -s [URI]`  
    Secret URI to fetch credentials from. Format: `<provider>://<key>[/<env_var>]`  
    Example: `conjur://mysecret/MY_ENV_VAR`  
    Can be specified multiple times for multiple secret URIs.
  - `--get-secrets-from-env, -si`  
    Fetch secrets from environment variables. If set, will use all environment variables that match the format `<env_var>=<provider>://<key>`  
    Example: `MY_ENV_VAR=conjur://mysecret`
  - `ARGV`  
    Command and arguments to start an MCP server.

  **Examples:**
  ```
  # Start MCP proxy with audit logging for a specific MCP server
  agc mcp-proxy start --cap audit uvx mcp-server-fetch

  # Start with debug logging
  agc mcp-proxy start -d --cap audit uvx mcp-server-fetch
  
  # Start with secret URI injection
  agc mcp-proxy start --cap audit --secret-uri conjur://my-api-key/MY_API_KEY uvx mcp-server-fetch
  
  # Start with multiple secret URIs
  agc mcp-proxy start --cap audit -s conjur://my-api-key/MY_API_KEY -s aws://db-password/DB_PASSWORD uvx mcp-server-fetch
  
  # Start with secrets from environment variables
  agc mcp-proxy start --cap audit --get-secrets-from-env uvx mcp-server-fetch
  
  # Combine secret injection with other options
  agc mcp-proxy start -d --cap audit --secret-uri conjur://my-api-key/MY_API_KEY --get-secrets-from-env uvx mcp-server-fetch
  
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
  ```
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
  ```
  docker run -v /path/to/local/logs:/logs agc mcp-proxy start --cap audit <command>
  ```
  
  This ensures logs are preserved even after the container exits.

- #### **Secrets Injection**

  Agent Guard MCP Proxy supports automatic secrets injection to provide secure credential management for MCP servers. Secrets can be fetched from various providers and injected as environment variables before starting the MCP server.

  ##### Secret URI Format

  Secret URIs follow the format: `<provider>://<key>[/<env_var>]`

  - `provider`: The secret provider (e.g., `conjur`, `aws`, `gcp`)
  - `key`: The secret key/name in the provider
  - `env_var`: (Optional) The environment variable name to set. If not provided, defaults to the key name.

  **Examples:**
  ```
  conjur://my-api-key/MY_API_KEY
  aws://database-password/DB_PASSWORD
  gcp://service-account-key
  ```

  ##### Using Secret URIs

  Use the `--secret-uri` (or `-s`) option to specify individual secret URIs:

  ```
  # Single secret URI
  agc mcp-proxy start --secret-uri conjur://my-api-key/MY_API_KEY uvx mcp-server-fetch

  # Multiple secret URIs
  agc mcp-proxy start -s conjur://my-api-key/MY_API_KEY -s aws://db-password/DB_PASSWORD uvx mcp-server-fetch
  ```

  ##### Using Environment Variables

  Use the `--get-secrets-from-env` (or `-si`) flag to automatically fetch secrets from environment variables that match the secret URI format:

  ```
  # Set environment variables in the format: ENV_VAR=provider://key
  export MY_API_KEY=conjur://my-api-key
  export DB_PASSWORD=aws://database-password

  # Use the flag to fetch all matching environment variables
  agc mcp-proxy start --get-secrets-from-env uvx mcp-server-fetch
  ```

  ##### Combining Both Methods

  You can combine both methods to provide maximum flexibility:

  ```
  agc mcp-proxy start --secret-uri conjur://my-api-key/MY_API_KEY --get-secrets-from-env uvx mcp-server-fetch
  ```

  **Security Note:** Secrets are fetched at startup and injected as environment variables for the MCP server process. Ensure your secret providers are properly configured and accessible.

- #### **Integration with Claude Desktop / Amazon Q CLI**

  You can configure Claude Desktop / Amazon Q CLI to use the Agent Guard MCP Proxy by creating a configuration file:

  **Basic Configuration:**
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

  **Configuration with Secrets Injection:**
  ```json
  {
    "mcpServers": {
      "agc_proxy_with_secrets": {
        "command": "agc",
        "args": [
          "mcp-proxy",
          "start",
          "--cap",
          "audit",
          "--secret-uri",
          "conjur://my-api-key/MY_API_KEY",
          "--get-secrets-from-env",
          "uvx",
          "mcp-server-fetch"
        ]
      }
    }
  }
  ```

### **secrets**

Group of commands to manage secrets.

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
  ```
  # Retrieve a secret from the default namespace
  agc secrets get -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret
  
  # Retrieve a secret from a custom namespace
  agc secrets get -p AWS_SECRETS_MANAGER_PROVIDER -k my-secret -n production
  ```


  **Note:** When retrieving secrets, you must specify the same namespace used when storing the secret.

## Help

For help on any command, use the `--help` flag:

```
agc mcp-proxy start --help
```

