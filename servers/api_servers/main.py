import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from servers.api_servers.routers.config import config_router
from servers.api_servers.routers.default import default_router
from servers.api_servers.routers.environment_variables import environment_variables_router

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

favicon_path = str(
    os.path.join(
        Path(__file__).parent.parent.parent, 'resources', 'favicon.ico'))


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "**  The requested resource was not found."},
    )


app.include_router(default_router)
app.include_router(config_router)
app.include_router(environment_variables_router)
