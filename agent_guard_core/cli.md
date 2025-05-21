# Agent Guard CLI

The Agent Guard CLI provides commands to configure and manage secret providers and related options for Agent Guard.

## Usage

```sh
agc [COMMAND] [OPTIONS]
```

## Commands

### configure

Group of commands to manage Agent Guard configuration.

#### set

Set the secret provider and related Conjur options.

**Options:**
- `--provider [PROVIDER]`  
  The secret provider to store and retrieve secrets.  
  Choices: `AWS_SECRETS_MANAGER_PROVIDER`, `FILE_SECRET_PROVIDER`, `CONJUR_SECRET_PROVIDER`  
  Default: `FILE_SECRET_PROVIDER`

- `--conjur_authn_login [LOGIN]`  
  (Optional) Conjur authentication login (workload ID).

- `--conjur_authn_api_key [API_KEY]`  
  (Optional) API Key to authenticate to Conjur Cloud.

- `--conjur_appliance_url [URL]`  
  (Optional) Endpoint URL of Conjur Cloud.

**Example:**
```sh
agc config set --provider CONJUR_SECRET_PROVIDER --conjur_authn_login my-app --conjur_authn_api_key my-key --conjur_appliance_url https://conjur.example.com
```

#### list

List all configuration parameters and their values.

**Example:**
```sh
agc config list
```

## Help

For help on any command, use the `--help` flag:

```sh
agc config set --help
```

---

**Note:**  
The CLI stores configuration in a file under your home directory: `~/.agent_guard/config.env`
