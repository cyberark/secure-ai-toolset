
<p style="text-align: center;">
    <img src="https://raw.githubusercontent.com/cyberark/agent-guard/refs/heads/main/resources/logo.png" alt="agentwatch - AI Agent Observability Platform" width="400"/>
    
</p>
<h3 style="font-family: 'Fira Mono', Monospace; text-align: center;">Docker container for AI agents</h3>




## 🌟 Overview

CyberArk's Agent Guard for Secret Retrieval (dockerized) is built for AI agent developers, and can be used to  streamline secret retrieval and reduce boilerplate. 

The tool uses the [Agent Guard CLI](../agent_guard_core/cli.md). 

Agent Guard is packaged as a Docker image which is available from the [AWS Marketplace](https://link.to.aws.marketplace.com). **!!!NEED TO UPDATE IMAGE NAME ADD LINK TO AWS MARKETPLACE!!!!.**



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
- You have at least one secret stored in your AWS Secrets Manager; for example: a secret named **secret1** with value **1234567890**.
- You have a working Docker setup
- You've downloaded the Agent Guard Docker image, `<name of image>`, from the AWS Marketplace


## 1. Set up the dockerized Agent Guard

1. Pull the Agent Guard for Secrets Retrieval image (**agc**) from AWS ECR.
2. Tag the image locally: `docker build -t agc`.

## 2. Retrieve a secret
Run the container to fetch the secret. For example, if you are using AWS Secrets Manager:

````
   export MY_SECRET=$(docker run \
     -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
     -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
     -e AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
     -e AWS_REGION=$AWS_REGION \
     agc secrets get \
     -p aws-secretsmanager \
     -k secret1)
    
````

   You can now use $MY_SECRET in your scripts or application.

## Key Features

### ✨ Supported secret providers

Currently supported [secret providers](https://github.com/cyberark/agent-guard/tree/main/agent_guard_core/credentials):
- AWS Secrets Manager
- CyberArk Secrets Manager (previously called CyberArk Conjur)


## 🤝 Contribution

Make sure to read the [CONTRIBUTING.md](https://github.com/cyberark/agent-guard/blob/main/CONTRIBUTING.md) file if you want to contribute to this project.

## 💁  Contact

Feel free to contact us via GitHub issues or through LinkedIn: [Gil Adda](https://www.linkedin.com/in/gil-adda-6117b9/), [Rafi Schwarz](https://www.linkedin.com/in/rafi-schwarz/).

