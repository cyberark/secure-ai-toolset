from fastapi import APIRouter
from fastapi.responses import HTMLResponse

default_router = APIRouter()
page_content = """
<h1>Agent Guard REST API Server</h1>
"""


@default_router.get("/")
async def default_route():
    return HTMLResponse(status_code=404, content=page_content)
