from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp import types
from mcp.types import TextResourceContents
from mcp_proxy.proxy_server import create_proxy_server


@pytest.mark.asyncio
async def test_proxy_server_all_methods_full_fields():
    # Mock remote_app with all capabilities enabled
    remote_app = MagicMock()
    remote_app.initialize = AsyncMock(return_value=MagicMock(
        capabilities=MagicMock(
            prompts=True,
            resources=True,
            logging=True,
            tools=True
        ),
        serverInfo=MagicMock(name="TestServer")
    ))

    # Prompts
    remote_app.list_prompts = AsyncMock(return_value=types.ListPromptsResult(
        prompts=[
            types.Prompt(name="prompt1", description="desc1"),
            types.Prompt(name="prompt2", description="desc2")
        ]
    ))
    remote_app.get_prompt = AsyncMock(return_value=types.GetPromptResult(
        description="Prompt 1 description",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(text="prompt1 result", type="text")
            )
        ]
    ))

    # Resources
    remote_app.list_resources = AsyncMock(return_value=types.ListResourcesResult(
        resources=[
            types.Resource(
                uri="resource://1",
                type="file",
                name="Resource1",
                description="A resource description",
                metadata={"key": "value"}
            )
        ]
    ))
    remote_app.list_resource_templates = AsyncMock(return_value=types.ListResourceTemplatesResult(
          resourceTemplates=[
              types.ResourceTemplate(
                  name="template1",
                  description="A template description",
                  fields={"field1": {"type": "string", "description": "A field"}},
                  uriTemplate="resource://{field1}"
              )
          ]
    ))
    remote_app.read_resource = AsyncMock(return_value=types.ReadResourceResult(
        contents=[
            TextResourceContents(
                uri="file:///tmp/test.txt",
                mimeType="text/plain",
                text="Sample file content"
            )
        ]
    ))
    remote_app.subscribe_resource = AsyncMock(return_value=types.EmptyResult())
    remote_app.unsubscribe_resource = AsyncMock(return_value=types.EmptyResult())
    #
    # # Logging
    remote_app.set_logging_level = AsyncMock(return_value=types.EmptyResult())
    #
    # # Tools
    remote_app.list_tools = AsyncMock(return_value=types.ListToolsResult(
        tools=[
            types.Tool(
                name="tool1",
                description="desc",
                arguments={"arg1": {"type": "string", "description": "argument 1"}},
                inputSchema={
                    "type": "object",
                    "properties": {
                        "arg1": {
                            "type": "string",
                            "description": "argument 1"
                        }
                    },
                    "required": ["arg1"]
                }
            )
        ]
    ))
    remote_app.call_tool = AsyncMock(return_value=types.CallToolResult(
        content=[types.TextContent(text="tool output", type="text")],
        isError=False
    ))

    # Completion
    remote_app.complete = AsyncMock(return_value=types.CompleteResult(
        completion=types.Completion(
            values=["complete!"],
            total=1,
            hasMore=False
        )
    ))

    # Progress notification
    remote_app.send_progress_notification = AsyncMock()


    app = await create_proxy_server(remote_app)

    # Prompts
    req = types.ListPromptsRequest(method="prompts/list")
    result = await app.request_handlers[types.ListPromptsRequest](req)
    assert [p["name"] for p in result.model_dump().get("prompts")] == ["prompt1", "prompt2"]

    get_prompt_req = types.GetPromptRequest(
        method="prompts/get",
        params=types.GetPromptRequestParams(name="prompt1", arguments={})
    )
    result = await app.request_handlers[types.GetPromptRequest](get_prompt_req)
    assert result.model_dump()["messages"][0]["content"]["text"] == "prompt1 result"
    #
    # Resources
    list_resources_req = types.ListResourcesRequest(method="resources/list")
    result = await app.request_handlers[types.ListResourcesRequest](list_resources_req)
    assert str(result.model_dump()["resources"][0]["uri"]) == "resource://1"
    assert result.model_dump()["resources"][0]["metadata"] == {"key": "value"}

    list_templates_req = types.ListResourceTemplatesRequest(method="resources/templates/list")
    result = await app.request_handlers[types.ListResourceTemplatesRequest](list_templates_req)
    result_dict = result.model_dump()
    assert result_dict["meta"] is None
    assert result_dict["nextCursor"] is None
    template = result_dict["resourceTemplates"][0]
    assert template["uriTemplate"] == "resource://{field1}"
    assert template["name"] == "template1"
    assert template["description"] == "A template description"
    assert template["mimeType"] is None
    assert template["annotations"] is None
    assert template["fields"] == {"field1": {"type": "string", "description": "A field"}}

    read_resource_req = types.ReadResourceRequest(
        method="resources/read",
        params=types.ReadResourceRequestParams(uri="resource://1")
    )
    result = await app.request_handlers[types.ReadResourceRequest](read_resource_req)
    result_dict = result.model_dump()
    assert result_dict["meta"] is None
    content = result_dict["contents"][0]
    assert str(content["uri"]) == "file:///tmp/test.txt"
    assert content["mimeType"] == "text/plain"
    assert content["text"] == "Sample file content"

    subscribe_req = types.SubscribeRequest(
        method="resources/subscribe",
        params=types.SubscribeRequestParams(uri="resource://1")
    )
    result = await app.request_handlers[types.SubscribeRequest](subscribe_req)
    assert result.model_dump()["meta"] is None

    unsubscribe_req = types.UnsubscribeRequest(
        method="resources/unsubscribe",
        params=types.UnsubscribeRequestParams(uri="resource://1")
    )
    result = await app.request_handlers[types.UnsubscribeRequest](unsubscribe_req)
    assert result.model_dump()["meta"] is None

    # Logging
    set_level_req = types.SetLevelRequest(
        method="logging/setLevel",
        params=types.SetLevelRequestParams(level="info")
    )
    result = await app.request_handlers[types.SetLevelRequest](set_level_req)
    assert result.model_dump()["meta"] is None
    # # Tools
    list_tools_req = types.ListToolsRequest(method="tools/list")
    result = await app.request_handlers[types.ListToolsRequest](list_tools_req)
    result_dict = result.model_dump()
    assert result_dict["meta"] is None
    assert result_dict["nextCursor"] is None
    assert result_dict["tools"][0]["name"] == "tool1"
    assert result_dict["tools"][0]["arguments"] == {"arg1": {"type": "string", "description": "argument 1"}}
    #
    call_tool_req = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name="tool1", arguments={})
    )
    result = await app.request_handlers[types.CallToolRequest](call_tool_req)
    assert result.model_dump()["content"][0]["type"] == "text"
    assert result.model_dump()["content"][0]["text"] == "tool output"

    # Complete
    complete_req = types.CompleteRequest(
        method="completion/complete",
        params=types.CompleteRequestParams(
            ref=types.ResourceReference(type="ref/resource", uri="resource://1"),
            argument=types.CompletionArgument(name="arg1", value="val1")
        )
    )
    result = await app.request_handlers[types.CompleteRequest](complete_req)
    result_dict = result.model_dump()
    assert result_dict["meta"] is None
    completion = result_dict["completion"]
    assert completion["values"] == ["complete!"]
    assert completion["total"] == 1
    assert completion["hasMore"] is False

    # Progress notification
    progress_notification = types.ProgressNotification(
        method="notifications/progress",
        params={
            "progressToken": "token1",
            "progress": 50,
            "total": 100
        }
    )
    await app.notification_handlers[types.ProgressNotification](progress_notification)
    remote_app.send_progress_notification.assert_awaited_with("token1", 50, 100)
