
<p style="text-align: center;">
    <img src="https://raw.githubusercontent.com/cyberark/agent-guard/refs/heads/main/resources/logo.png" alt="agentwatch - AI Agent Observability Platform" width="400"/>
    
</p>
<h3 style="font-family: 'Fira Mono', Monospace; text-align: center;">MCP Proxy for AI agents</h3>

## 🌟 Overview

CyberArk's Agent Guard MCP Proxy is an AI agent security tool built for developers and has full auditing and monitoring capabilities. Every interaction between the AI agent and your MCP servers is logged, providing complete traceability and compliance with enterprise security standards.

The tool uses the [Agent Guard CLI](../agent_guard_core/cli.md).

The Docker image, `<name>`, is available from the [AWS Marketplace](https://link.to.aws.marketplace.com).  **!!!NEED TO UPDATE IMAGE NAME ADD LINK TO AWS MARKETPLACE!!!!.**


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
2. Tag the image locally: `docker build -t agc`.

## 2. Generate configuration snippets for audit logging

Set up a local sample config file (e.g., /tmp/config/config-sample.json).

Mount the config file's directory to the container's /config path and run apply-config -c audit to apply the audit capabilities to this sample config file:

````
docker run -v /tmp/config:/config agc mcp-proxy apply-config -c audit
````

## 3. Update the AI agent's MCP configuration

From the output, copy the audit capabilities that interest you into your AI agent’s `<mcp-config>.json` file.

## 4. Set up the log file

Logs are written to **agent_guard_core_proxy.log**. To see the logs locally, mount a local path to the Docker container's /logs path.

For example: 
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
