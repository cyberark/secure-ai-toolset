
<p style="text-align: center;">
    <img src="https://raw.githubusercontent.com/cyberark/agent-guard/refs/heads/main/resources/logo.png" alt="agentwatch - AI Agent Observability Platform" width="400"/>
    
</p>
<h3 style="font-family: 'Fira Mono', Monospace; text-align: center;">MCP Proxy for AI agents</h3>

## 🌟 Overview

CyberArk's Agent Guard MCP Proxy is an AI agent security tool built for developers and has full auditing and monitoring capabilities. Every interaction between the AI agent and your MCP servers is logged, providing complete traceability and compliance with enterprise security standards.

The tool uses the [Agent Guard CLI](../agent_guard_core/cli.md).

The Docker image, `cyberark/cyberark.agent-guard:1.0.1`, is available from the [AWS Marketplace](https://link.to.aws.marketplace.com).  **!!!NEED TO UPDATE IMAGE NAME ADD LINK TO AWS MARKETPLACE!!!!.**


## Before you begin

Make sure that:

- You're authenticated to AWS and you've set up the following environment variables for AWS authentication, including their values, in your CLI:

   #### Example

   ````
   export AWS_ACCESS_KEY_ID="your-aws-access-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_SESSION_TOKEN="your-aws-token" 
   export AWS_REGION="your-region"  
   ````
- You have a working Docker setup
- You've downloaded the Agent Guard Docker image, `<name of image>`, from the AWS Marketplace


## 1. Set up the dockerized Agent Guard

1. Pull the Agent Guard MCP Proxy image (**agc**) from AWS ECR.
```
docker pull 709825985650.dkr.ecr.us-east-1.amazonaws.com/cyberark/cyberark.agent-guard:1.0.1
```
2. Tag the image locally: 
```
docker tag 709825985650.dkr.ecr.us-east-1.amazonaws.com/cyberark/cyberark.agent-guard:1.0.1 agc
```
## 2. Enable Agent Guard MCP Proxy in your existing configurations

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

````
docker run -v /home/user/:/config agc mcp-proxy apply-config -c audit
````

Agent Guard will automatically scan the folder for any relevant JSON files and modify it to the Agent Guard MCP Proxy, and output the
modified configuration file.

## 3. Update the AI agent's MCP configuration

From the output, copy the audit capabilities that interest you into your AI agent’s `<mcp-config>.json` file.

## 4. Set up the log file

Logs are written to **agent_guard_core_proxy.log**, and is written under /logs insides the container. For you to see it,
make sure you mount the /logs directory. 

For example, this will cause the looks to be written to /tmp/agent_guard_core_proxy.log on the host:
````
docker run -v /tmp:/logs
````


## Example

Set up a configuration file, **config-sample.json**, locally in **/tmp/config**.

Run the following to apply the Agent Guard's audit capabilities to your config-sample file.

 ````
docker run -v /tmp/config:/config agc mcp-proxy apply-config -c audit
````

#### Output:
![apply-config](/docs/images/mcp-proxy-apply-config.png)


Copy over to your AI agent's MCP config file the activity you want to log. For example, `fetch` logs request and response activity between your AI agent and the MCP server you are working with:

![ai-agent-config](/docs/images/mcp-proxy-ai-agent-config.png)


### Log output
When you run your MCP host, you should start seeing the host interacting with the proxied MCP server querying it for the List operations like this:

![log](/docs/images/output.png)

As you interact with the server, you should see more logs:

![server-interaction-logs](/docs/images/output-server-interaction.png)
