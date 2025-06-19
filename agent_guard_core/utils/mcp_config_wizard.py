import json
from typing import Any, List, Optional


def transform_mcp_servers(file_name: str, capabilities: Optional[List[str]] = None) -> dict[str, Any]:
    """Load and transform an MCP servers JSON file."""
    if capabilities is None:
        capabilities = []
    
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

        if 'url' in server_config:
            transform_remote_server(server_config, capabilities)
        elif server_config.get('command') is not None:
            transform_stdio_server(server_config, capabilities)
        else:
            # Skip unsupported server types
            continue

    return data


def transform_stdio_server(server_config: dict[str, Any], capabilities: List[str]) -> None:
    """Transform a local stdio server config to docker run format."""
    env_args = []
    env = server_config.get('env', {})

    for key, _ in env.items():
        env_args.extend(["-e", f"{key}"])

    command = server_config['command']
    args = server_config.get('args', [])
    
    # Start with the basic command
    new_args = ["run", "-i"] + env_args + ["agc", "mcp-proxy", "start"]
    
    # Add capabilities if provided
    for cap in capabilities:
        new_args.extend(["-c", cap])
    
    # Add the original command and args
    new_args.extend([command] + args)

    server_config["command"] = "docker"
    server_config["args"] = new_args


def transform_remote_server(server_config: dict[str, Any], capabilities: List[str]) -> None:
    """Transform a remote URL-based MCP server config."""
    url = server_config.pop('url')
    headers = server_config.pop('headers', {})  # remove headers if exists

    env_args = []
    env = server_config.get('env', {})

    for key, _ in env.items():
        env_args.extend(["-e", f"{key}"])

    header_args = []
    for key, value in headers.items():
        header_args.extend(["--header", f"{key}: {value}"])

    # Start with the basic command
    new_args = ["run"] + env_args + ["agc", "mcp-proxy", "start"]
    
    # Add capabilities if provided
    for cap in capabilities:
        new_args.extend(["-c", cap])
    
    # Add the original command and args
    new_args.extend(["uvx", "mcp-remote", url] + header_args)

    server_config["command"] = "docker"
    server_config["args"] = new_args

    if 'transportType' in server_config:
        server_config['transportType'] = 'stdio'
