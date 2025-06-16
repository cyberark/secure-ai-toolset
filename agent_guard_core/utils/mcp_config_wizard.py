import json


def transform_mcp_servers(file_name: str) -> dict:
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {e}")

    if 'mcpServers' not in data or not isinstance(data['mcpServers'], dict):
        raise ValueError("JSON must contain a 'mcpServers' key with an object as its value.")

    for server_name, server_config in data['mcpServers'].items():
        if not isinstance(server_config, dict):
            raise ValueError(f"Server config for '{server_name}' must be a dictionary.")

        if (command := server_config.get('command')) is None: # No support for non-stdio mcp servers
            continue

        # Extract env as docker -E arguments
        env_args = []
        env = server_config.get('env', {})
        if not isinstance(env, dict):
            raise ValueError(f"'env' field in server '{server_name}' must be a dictionary.")
        
        for key, value in env.items():
            env_args.extend(["-E", f"{key}={value}"])

        # Build the new args
        new_args = ["run", "-i", "agc", "proxy", "start", command] + env_args + server_config.get("args", [])

        # Update the server config
        server_config["command"] = "docker"
        server_config["args"] = new_args
        server_config["env"] = {}  # Clear env since it's now handled in args

    return data

if __name__ == "__main__":
    updated_json = transform_mcp_servers("/Users/shaid/Desktop/sources/agent-guard/config_example.json")
    print(json.dumps(updated_json, indent=2))