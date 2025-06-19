"""Create an MCP server that proxies requests through an MCP client.

This server is created independent of any transport mechanism.
"""

import logging
import typing as t

from mcp import ListResourcesResult, server, types
from mcp.client.session import ClientSession
from mcp.types import CompleteResult, ListResourceTemplatesResult, ListToolsResult, ReadResourceResult

from agent_guard_core.proxy.proxy_utils import audit_log_operation

logger = logging.getLogger(__name__)

async def create_agent_guard_proxy_server(remote_app: ClientSession, audit_logger: t.Optional[logging.Logger] = None) -> server.Server[object]:  # noqa: C901, PLR0915
    """Create a server instance from a remote app."""
    if audit_logger is None:
        audit_logger = logging.getLogger("null")
        audit_logger.addHandler(logging.NullHandler())

    logger.debug("Sending initialization request to remote MCP server...")
    response = await remote_app.initialize()
    capabilities = response.capabilities

    logger.debug("Configuring proxied MCP server...")
    app: server.Server[object] = server.Server(name=response.serverInfo.name)

    if capabilities.prompts:
        logger.debug("Capabilities: adding Prompts...")

        @audit_log_operation(audit_logger, "ListPrompts")
        async def _list_prompts(_: t.Any) -> types.ServerResult:  # noqa: ANN401
            result = await remote_app.list_prompts()
            return types.ServerResult(result)

        app.request_handlers[types.ListPromptsRequest] = _list_prompts

        @audit_log_operation(audit_logger, "GetPrompt")
        async def _get_prompt(req: types.GetPromptRequest) -> types.ServerResult:
            result = await remote_app.get_prompt(req.params.name, req.params.arguments)
            return types.ServerResult(result)

        app.request_handlers[types.GetPromptRequest] = _get_prompt

    if capabilities.resources:
        logger.debug("Capabilities: adding Resources...")

        @audit_log_operation(audit_logger, "ListResources")
        async def _list_resources(_: t.Any) -> types.ServerResult:  # noqa: ANN401
            result: ListResourcesResult = await remote_app.list_resources()
            return types.ServerResult(result)

        app.request_handlers[types.ListResourcesRequest] = _list_resources

        @audit_log_operation(audit_logger, "ListResourceTemplates")
        async def _list_resource_templates(_: t.Any) -> types.ServerResult:  # noqa: ANN401
            result: ListResourceTemplatesResult = await remote_app.list_resource_templates()
            return types.ServerResult(result)

        app.request_handlers[types.ListResourceTemplatesRequest] = _list_resource_templates

        @audit_log_operation(audit_logger, "ReadResource")
        async def _read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
            result: ReadResourceResult = await remote_app.read_resource(req.params.uri)
            return types.ServerResult(result)

        app.request_handlers[types.ReadResourceRequest] = _read_resource

    if capabilities.logging:
        logger.debug("Capabilities: adding Logging...")

        async def _set_logging_level(req: types.SetLevelRequest) -> types.ServerResult:
            await remote_app.set_logging_level(req.params.level)
            return types.ServerResult(types.EmptyResult())

        app.request_handlers[types.SetLevelRequest] = _set_logging_level

    if capabilities.resources:
        logger.debug("Capabilities: adding Resources...")

        @audit_log_operation(audit_logger, "SubscribeResource")
        async def _subscribe_resource(req: types.SubscribeRequest) -> types.ServerResult:
            await remote_app.subscribe_resource(req.params.uri)
            return types.ServerResult(types.EmptyResult())

        app.request_handlers[types.SubscribeRequest] = _subscribe_resource

        @audit_log_operation(audit_logger, "UbsubscribeResource")
        async def _unsubscribe_resource(req: types.UnsubscribeRequest) -> types.ServerResult:
            await remote_app.unsubscribe_resource(req.params.uri)
            return types.ServerResult(types.EmptyResult())

        app.request_handlers[types.UnsubscribeRequest] = _unsubscribe_resource

    if capabilities.tools:
        logger.debug("Capabilities: adding Tools...")

        @audit_log_operation(audit_logger, "ListTools")
        async def _list_tools(_: t.Any) -> types.ServerResult:  # noqa: ANN401
            tools: ListToolsResult = await remote_app.list_tools()
            return types.ServerResult(tools)

        app.request_handlers[types.ListToolsRequest] = _list_tools

        @audit_log_operation(audit_logger, "CallTool")
        async def _call_tool(req: types.CallToolRequest) -> types.ServerResult:
            logger.debug(f"Calling tool...{req.params.name}")
            try:
                result: types.CallToolResult = await remote_app.call_tool(
                    req.params.name,
                    (req.params.arguments or {}),
                )
                return types.ServerResult(result)
            except Exception as e:  # noqa: BLE001
                return types.ServerResult(
                    types.CallToolResult(
                        content=[types.TextContent(type="text", text=str(e))],
                        isError=True,
                    ),
                )

        app.request_handlers[types.CallToolRequest] = _call_tool

    async def _send_progress_notification(req: types.ProgressNotification) -> None:
        await remote_app.send_progress_notification(
            req.params.progressToken,
            req.params.progress,
            req.params.total,
        )

    app.notification_handlers[types.ProgressNotification] = _send_progress_notification

    async def _complete(req: types.CompleteRequest) -> types.ServerResult:
        result: CompleteResult = await remote_app.complete(
            req.params.ref,
            req.params.argument.model_dump(),
        )
        return types.ServerResult(result)

    app.request_handlers[types.CompleteRequest] = _complete

    return app
