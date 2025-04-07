from fastapi import FastAPI
from routers import secrets

app = FastAPI(
    title="AgentGuard",
    description="AgentGuard API for prompt sanitization and management.",
    summary="A robust API for sanitizing and managing prompts.",
    version="1.0.0",
    terms_of_service="http://agentguard.example.com/terms/",
    contact={
        "name": "AgentGuard Support",
        "url": "http://agentguard.example.com/contact/",
        "email": "support@agentguard.example.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

#
app.include_router(secrets.router)
