
# Agent Guard for AI Agents (Containerized)

- [Overview](#overview)
- [Before you begin](#before-you-begin)
- [Audit and monitor with the MCP Proxy](#audit-and-monitor-with-the-mcp-proxy)
- [Retrieve a secret](#retrieve-a-secret)


## Overview

CyberArk's Agent Guard is an AI agent security tool supporting secure secret retrieval for agents managed via external secret providers such as AWS Secrets Manager and CyberArk Secrets Manager (prevfiously CyberArk Conjur).Conjur Open Source, and traceability of AI agent MCP communications via the Agent Guard’s MCP Proxy.

The tool uses the [Agent Guard CLI](../agent_guard_core/cli.md).

The Agent Guard Docker image is available from the Amazon ECR which is accessible through the AWS Marketplace.

## Before you begin

### 1. Make sure that:

- You're authenticated to AWS and you've set up the following environment variables for AWS authentication, including their values, in your CLI:

   #### Example

   ```
   export AWS_ACCESS_KEY_ID="your-aws-access-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_SESSION_TOKEN="your-aws-token" 
   export AWS_REGION="your-region"  
   ```
- You have a working Docker setup
- You've downloaded the Agent Guard Docker image, `<name of image>`, from the AWS Marketplace

### 2. Set up the Agent Guard container

1. Pull the Agent Guard Docker image (**agc**) from the Amazon ECR.
```
docker pull 709825985650.dkr.ecr.us-east-1.amazonaws.com/cyberark/cyberark.agent-guard:1.0.1
```
2. Tag the image locally: 
```
docker tag 709825985650.dkr.ecr.us-east-1.amazonaws.com/cyberark/cyberark.agent-guard:1.0.1 agc
```

## Audit and monitor with the MCP Proxy
CyberArk's Agent Guard MCP Proxy is an AI agent security tool built for developers and has full auditing and monitoring capabilities. Every interaction between the AI agent and your MCP servers is logged, providing complete traceability and compliance with enterprise security standards.

### 1. Enable the Agent Guard MCP Proxy in your existing configuration

Agent Guard offers an 'apply-config' command which automatically enables the Agent Guard MCP Proxy in your existing configuration.
You can also elect to make the changes manually, by prepending 'docker run agc' to your MCP server configuration block:
An example config of an MCP client which looks like this:
```
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": [
        "mcp-server-fetch"
      ],
      "transportType": "stdio"
    }
  }
}
```

turns into:

```
{
  "mcpServers": {
    "fetch": {
      "command": "docker",
      "args": [
        "run",
        "agc",
        "mcp-proxy",
        "start",
        "-c",
        "audit",
        "uvx",
        "mcp-server-fetch
      ],
      "transportType": "stdio"
    }
  }
}
```

If you want to use the 'apply-config' command, locate the path of your MCP server configuration file (let's call it /home/user/mcpservers.json for the same of the example), and run the following command:

```
docker run -v /home/user/:/config agc mcp-proxy apply-config -c audit
```

Agent Guard will automatically scan the folder for any relevant JSON files and modify it to the Agent Guard MCP Proxy, and output the
modified configuration file.

### 2. Update the AI agent's MCP configuration

From the output, copy the audit capabilities that interest you into your AI agent’s `<mcp-config>.json` file.

### 3. Set up the log file

Logs are written to **agent_guard_core_proxy.log**, and is written under /logs insides the container. For you to see it,
make sure you mount the /logs directory. 

For example, this will cause the looks to be written to /tmp/agent_guard_core_proxy.log on the host:
```
docker run -v /tmp:/logs
```

### Example

Set up a configuration file, **config-sample.json**, locally in **/tmp/config**.

Run the following to apply the Agent Guard's audit capabilities to your config-sample file.

```
docker run -v /tmp/config:/config agc mcp-proxy apply-config -c audit
```

#### Output:
![apply-config](/docs/images/mcp-proxy-apply-config.png)


Copy over to your AI agent's MCP config file the activity you want to log. For example, `fetch` logs request and response activity between your AI agent and the MCP server you are working with:

![ai-agent-config](/docs/images/mcp-proxy-ai-agent-config.png)

### Log output
When you run your MCP host, you should start seeing the host interacting with the proxied MCP server querying it for the List operations like this:

![log](/docs/images/output.png)

As you interact with the server, you should see more logs:

![server-interaction-logs](/docs/images/output-server-interaction.png)

## Retrieve a secret

CyberArk's Agent Guard for Secret Retrieval (dockerized) is built for AI agent developers, and can be used to  streamline secret retrieval and reduce boilerplate. 

Make sure you have at least one secret stored in your Secrets Manager; for example: a secret named **secret1** with value **1234567890**.

Run the container to fetch the secret. For example, if you are using AWS Secrets Manager:

```
   export MY_SECRET=$(docker run \
     -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
     -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
     -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
     -e AWS_REGION=$AWS_REGION \
     agc secrets get \
     -p aws-secretsmanager \
     -k secret1)
    
```

   You can now use $MY_SECRET in your scripts or application.