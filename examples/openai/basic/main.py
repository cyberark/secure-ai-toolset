from openai import OpenAI

from agent_guard_core.credentials.environment_manager import EnvironmentVariablesManager
from agent_guard_core.credentials.file_secrets_provider import FileSecretsProvider

with EnvironmentVariablesManager(
        FileSecretsProvider("/Users/gil.adda/Music/demo.env")):
    
    client = OpenAI()

    # 
    # Use this code if you face an enterprise MITM proxy re-signing the certificates
    # and you want to disable SSL certificate verification
    # 
    # httpx_client = httpx.Client(http2=True, verify=False)
    # client = OpenAI(http_client=httpx_client)

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role":
            "user",
            "content":
            "Write a one-sentence bedtime story about a unicorn."
        }])

print(completion.choices[0].message.content)
