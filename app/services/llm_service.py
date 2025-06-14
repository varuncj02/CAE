import json
import re
import uuid
from typing import Any

from openai import AsyncOpenAI
from openai.types.chat.chat_completion import ChatCompletion

from utils.config import app_settings
from utils.logger import logger
from utils.exceptions import LLMException
from schema.llm.message import Message, ToolMessage
from schema.llm.tool import AbstractTool, ToolCall


def collect_tools() -> dict[str, dict[str, Any]]:
    """
    Collects all AbstractTool subclasses and their schemas/functions.
    Returns a dictionary mapping tool names to their details.
    """
    tools = {}

    for tool_class in AbstractTool.__subclasses__():
        try:
            tool_name = tool_class.__name__

            tools[tool_name] = {
                "class": tool_class,
                "schema": tool_class.tool_schema,
                "function": tool_class.tool_function(),
            }

            logger.debug(f"Collected tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to collect tool {tool_class.__name__}: {str(e)}")
            continue

    return tools


def clean_json_response(response: str) -> dict:
    try:
        match = re.search(r"```(?:json)?(.*?)```", response, re.DOTALL)
        if match is None:
            return json.loads(response)
        json_content = match.group(1).strip()
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}\n\nResponse: {response}")
        raise LLMException(
            f"Failed to parse JSON response: {e}\n\nResponse: {response}"
        ) from e


class LLMService:
    def __init__(
        self,
        base_url: str = app_settings.LLM_API_BASE_URL,
        api_key: str = app_settings.LLM_API_KEY,
        model_name: str = app_settings.LLM_MODEL_NAME,
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name

        self.tools: dict[str, dict[str, Any]] = collect_tools()
        logger.debug(f"Initialized LLMService with {len(self.tools)} tools")

    def _client(self) -> AsyncOpenAI:
        return AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    async def query_llm(
        self,
        messages: Message | list[Message],
        json_response: bool = False,
        tools: str | list[str] | None = None,
        **kwargs,
    ) -> Message:
        """
        Query the LLM with messages and optional tools.

        Args:
            messages: Single message or list of messages to send to LLM
            json_response: Whether to request JSON formatted response
            tools: Tool name(s) to make available to LLM
            **kwargs: Additional parameters for the LLM API

        Returns:
            Message response from LLM or parsed JSON if json_response=True

        Raises:
            LLMException: If LLM query fails or response parsing fails
        """
        request_id = f"msg_{str(uuid.uuid4())}"

        logger.info(
            "Starting LLM query",
            extra={
                "request_id": request_id,
                "json_response": json_response,
                "tools_requested": tools,
                "message_count": len(messages) if isinstance(messages, list) else 1,
                "model": self.model_name,
            },
        )

        try:
            normalized_messages = self._normalize_messages(messages)
            prepared_tools = self._prepare_tools(tools, request_id)

            completion = await self._make_llm_request(
                normalized_messages, prepared_tools, json_response, request_id, **kwargs
            )

            if completion.choices[0].message.tool_calls:
                completion = await self._handle_tool_workflow(
                    completion, normalized_messages, json_response, request_id, **kwargs
                )

            return self._process_response(completion, json_response, request_id)

        except Exception as e:
            logger.error(
                "LLM query failed",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "json_response": json_response,
                    "tools": tools,
                },
            )
            if isinstance(e, LLMException):
                raise
            raise LLMException(f"Failed to query LLM: {e}") from e

    def _normalize_messages(self, messages: Message | list[Message]) -> list[Message]:
        """Convert single message to list format."""
        if isinstance(messages, Message):
            return [messages]
        return messages

    def _prepare_tools(
        self, tools: str | list[str] | None, request_id: uuid.UUID
    ) -> list[dict] | None:
        """
        Prepare tools for LLM request.

        Args:
            tools: Tool name(s) to prepare
            request_id: Request ID for logging

        Returns:
            List of tool schemas or None if no tools

        Raises:
            ValueError: If unknown tool is requested
        """
        if not tools:
            return None

        if isinstance(tools, str):
            tools = [tools]

        tools_to_call = []
        for tool in tools:
            if tool not in self.tools:
                logger.error(
                    "Unknown tool requested",
                    extra={
                        "request_id": request_id,
                        "unknown_tool": tool,
                        "available_tools": list(self.tools.keys()),
                    },
                )
                raise ValueError(f"Unknown tool: {tool}")

            tool_schema = self.tools[tool]["schema"].model_dump(exclude_none=True)
            tools_to_call.append(tool_schema)

            logger.debug(
                "Tool prepared for LLM",
                extra={
                    "request_id": request_id,
                    "tool_name": tool,
                    "tool_schema": tool_schema,
                },
            )

        logger.info(
            "Tools prepared for LLM request",
            extra={
                "request_id": request_id,
                "tool_count": len(tools_to_call),
                "tool_names": tools,
            },
        )

        return tools_to_call

    async def _make_llm_request(
        self,
        messages: list[Message],
        tools: list[dict] | None,
        json_response: bool,
        request_id: uuid.UUID,
        **kwargs,
    ) -> ChatCompletion:
        """
        Make the actual LLM API request.

        Args:
            messages: Normalized list of messages
            tools: Prepared tool schemas
            json_response: Whether to request JSON response
            request_id: Request ID for logging
            **kwargs: Additional LLM parameters

        Returns:
            ChatCompletion response from LLM
        """
        client = self._client()

        request_params = {
            "model": self.model_name,
            "messages": messages,
            "tools": tools,
            "response_format": {"type": "json_object"} if json_response else None,
            **kwargs,
        }

        logger.debug(
            "Making LLM API request",
            extra={
                "request_id": request_id,
                "latest_message_content": messages[-1].get("content", "")[:200] + "..."
                if len(str(messages[-1].get("content", ""))) > 200
                else messages[-1].get("content", ""),
                "request_params": {
                    "model": request_params["model"],
                    "message_count": len(messages),
                    "tools_provided": len(tools) if tools else 0,
                    "json_response": json_response,
                    "additional_params": list(kwargs.keys()),
                },
            },
        )

        completion: ChatCompletion = await client.chat.completions.create(
            **request_params
        )

        logger.info(
            "LLM API request completed",
            extra={
                "request_id": request_id,
                "response_metadata": {
                    "model": completion.model,
                    "usage": completion.usage.model_dump()
                    if completion.usage
                    else None,
                    "finish_reason": completion.choices[0].finish_reason,
                    "has_tool_calls": bool(completion.choices[0].message.tool_calls),
                },
            },
        )
        return completion

    async def _handle_tool_workflow(
        self,
        initial_completion: ChatCompletion,
        messages: list[Message],
        json_response: bool,
        request_id: uuid.UUID,
        **kwargs,
    ) -> ChatCompletion:
        """
        Handle the complete tool calling workflow.

        Args:
            initial_completion: Initial LLM response with tool calls
            messages: Original messages
            json_response: Whether to request JSON response
            request_id: Request ID for logging
            **kwargs: Additional LLM parameters

        Returns:
            Final ChatCompletion after tool execution
        """
        tool_calls = initial_completion.choices[0].message.tool_calls

        logger.info(
            "Processing tool calls",
            extra={
                "request_id": request_id,
                "tool_call_count": len(tool_calls),
                "tool_calls": [
                    {
                        "id": call.id,
                        "function_name": call.function.name,
                        "arguments": call.function.arguments,
                    }
                    for call in tool_calls
                ],
            },
        )

        tool_results = await self.handle_tool_calls(tool_calls)

        logger.debug(
            "Tool execution completed",
            extra={
                "request_id": request_id,
                "tool_result_count": len(tool_results),
                "tool_results": [
                    {
                        "tool_call_id": result.tool_call_id,
                        "tool_name": result.name,
                        "success": "error" not in str(result.content),
                    }
                    for result in tool_results
                ],
            },
        )

        full_messages = (
            messages + [initial_completion.choices[0].message] + tool_results
        )

        logger.debug(
            "Making follow-up LLM request with tool results",
            extra={
                "request_id": request_id,
                "total_message_count": len(full_messages),
                "tool_result_count": len(tool_results),
            },
        )

        client = self._client()
        final_completion = await client.chat.completions.create(
            model=self.model_name,
            messages=full_messages,
            response_format={"type": "json_object"} if json_response else None,
            **kwargs,
        )

        logger.info(
            "Follow-up LLM request completed",
            extra={
                "request_id": request_id,
                "final_response_metadata": {
                    "model": final_completion.model,
                    "usage": final_completion.usage.model_dump()
                    if final_completion.usage
                    else None,
                    "finish_reason": final_completion.choices[0].finish_reason,
                    "has_tool_calls": bool(
                        final_completion.choices[0].message.tool_calls
                    ),
                },
            },
        )

        return final_completion

    def _process_response(
        self, completion: ChatCompletion, json_response: bool, request_id: uuid.UUID
    ) -> Message | dict:
        """
        Process the final LLM response.

        Args:
            completion: ChatCompletion from LLM
            json_response: Whether to parse as JSON
            request_id: Request ID for logging

        Returns:
            Processed response (Message or parsed JSON)

        Raises:
            LLMException: If JSON parsing fails
        """
        response_content = completion.choices[0].message.content

        if json_response:
            try:
                parsed_response = json.loads(response_content)
                logger.info(
                    "JSON response parsed successfully",
                    extra={
                        "request_id": request_id,
                        "response_keys": list(parsed_response.keys())
                        if isinstance(parsed_response, dict)
                        else None,
                        "response_type": type(parsed_response).__name__,
                    },
                )
                return parsed_response
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse JSON response",
                    extra={
                        "request_id": request_id,
                        "error": str(e),
                        "response_content": response_content[:500] + "..."
                        if len(response_content) > 500
                        else response_content,
                    },
                )
                raise LLMException(
                    f"Failed to parse JSON response: {e}\n\nResponse: {response_content}"
                ) from e
        else:
            logger.info(
                "Text response processed successfully",
                extra={
                    "request_id": request_id,
                    "response_length": len(response_content) if response_content else 0,
                    "response_preview": response_content[:200] + "..."
                    if response_content and len(response_content) > 200
                    else response_content,
                },
            )
            return completion.choices[0].message

    async def handle_tool_calls(self, tool_calls: list[ToolCall]) -> list[ToolMessage]:
        """
        Handle tool calls from the LLM response.

        Args:
            tool_calls: List of ToolCall objects from the LLM response

        Returns:
            List of ToolMessage objects with the results of tool execution
        """
        if not tool_calls:
            logger.debug("No tool calls to process")
            return []

        execution_id = f"tool_{str(uuid.uuid4())}"

        logger.info(
            "Starting tool execution batch",
            extra={
                "execution_id": execution_id,
                "tool_call_count": len(tool_calls),
                "tool_calls_summary": [
                    {
                        "id": call.id,
                        "function_name": call.function.name,
                        "has_arguments": bool(call.function.arguments),
                    }
                    for call in tool_calls
                ],
            },
        )

        results = []
        successful_calls = 0
        failed_calls = 0

        for call_index, call in enumerate(tool_calls):
            logger.debug(
                "Executing individual tool call",
                extra={
                    "execution_id": execution_id,
                    "call_index": call_index,
                    "tool_call_id": call.id,
                    "function_name": call.function.name,
                    "arguments": call.function.arguments,
                },
            )

            try:
                tool_result = await self._execute_single_tool_call(
                    call, execution_id, call_index
                )
                results.append(tool_result)
                successful_calls += 1

                logger.info(
                    "Tool call executed successfully",
                    extra={
                        "execution_id": execution_id,
                        "call_index": call_index,
                        "tool_call_id": call.id,
                        "function_name": call.function.name,
                        "result_preview": str(tool_result.content)[:200] + "..."
                        if len(str(tool_result.content)) > 200
                        else str(tool_result.content),
                    },
                )

            except Exception as e:
                failed_calls += 1
                error_result = self._create_error_tool_message(
                    call, e, execution_id, call_index
                )
                results.append(error_result)

        logger.info(
            "Tool execution batch completed",
            extra={
                "execution_id": execution_id,
                "total_calls": len(tool_calls),
                "successful_calls": successful_calls,
                "failed_calls": failed_calls,
                "success_rate": successful_calls / len(tool_calls) if tool_calls else 0,
            },
        )

        return results

    async def _execute_single_tool_call(
        self, call: ToolCall, execution_id: uuid.UUID, call_index: int
    ) -> ToolMessage:
        """
        Execute a single tool call.

        Args:
            call: The ToolCall object to execute
            execution_id: Execution batch ID for logging
            call_index: Index of this call in the batch

        Returns:
            ToolMessage with the result

        Raises:
            Exception: If tool execution fails
        """
        name = call.function.name

        try:
            args = json.loads(call.function.arguments)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse tool arguments",
                extra={
                    "execution_id": execution_id,
                    "call_index": call_index,
                    "tool_call_id": call.id,
                    "function_name": name,
                    "raw_arguments": call.function.arguments,
                    "error": str(e),
                },
            )
            raise ValueError(f"Invalid JSON in tool arguments: {e}") from e

        if name not in self.tools:
            logger.error(
                "Tool not found in available tools",
                extra={
                    "execution_id": execution_id,
                    "call_index": call_index,
                    "tool_call_id": call.id,
                    "requested_tool": name,
                    "available_tools": list(self.tools.keys()),
                },
            )
            raise ValueError(f"Tool '{name}' not found in available tools")

        tool_function = self.tools[name]["function"]

        logger.debug(
            "Executing tool function",
            extra={
                "execution_id": execution_id,
                "call_index": call_index,
                "tool_call_id": call.id,
                "function_name": name,
                "parsed_arguments": args,
            },
        )

        try:
            result = await tool_function(**args)

            tool_message = ToolMessage(
                role="tool",
                tool_call_id=call.id,
                name=name,
                content=result.json(),
            )

            logger.debug(
                "Tool function executed successfully",
                extra={
                    "execution_id": execution_id,
                    "call_index": call_index,
                    "tool_call_id": call.id,
                    "function_name": name,
                    "result_type": type(result).__name__,
                },
            )

            return tool_message

        except Exception as e:
            logger.error(
                "Tool function execution failed",
                extra={
                    "execution_id": execution_id,
                    "call_index": call_index,
                    "tool_call_id": call.id,
                    "function_name": name,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "arguments": args,
                },
            )
            raise

    def _create_error_tool_message(
        self, call: ToolCall, error: Exception, execution_id: uuid.UUID, call_index: int
    ) -> ToolMessage:
        """
        Create a ToolMessage for a failed tool call.

        Args:
            call: The failed ToolCall
            error: The exception that occurred
            execution_id: Execution batch ID for logging
            call_index: Index of this call in the batch

        Returns:
            ToolMessage with error information
        """
        logger.error(
            "Creating error tool message",
            extra={
                "execution_id": execution_id,
                "call_index": call_index,
                "tool_call_id": getattr(call, "id", "unknown"),
                "function_name": getattr(call.function, "name", "unknown")
                if hasattr(call, "function")
                else "unknown",
                "error": str(error),
                "error_type": type(error).__name__,
            },
        )

        return ToolMessage(
            role="tool",
            tool_call_id=getattr(call, "id", "unknown"),
            name=getattr(call.function, "name", "unknown")
            if hasattr(call, "function")
            else "unknown",
            content={"error": str(error), "error_type": type(error).__name__},
        )
