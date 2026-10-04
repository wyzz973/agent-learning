"""当前DeepSeek模型的有限原生HTTP设施；不提供本人消息编解码或agent循环。"""

from __future__ import annotations

import asyncio
import copy
import json
from typing import Any
from urllib.parse import urlparse

import httpx


def validate_wire_messages(messages: list[dict[str, Any]]) -> None:
    """核对有限文本消息及工具配对，外部内容不改变角色。

    Args:
        messages: system/user/assistant/tool文本消息；工具请求采用原生function格式。
    Returns:
        无；只检查协议，不调用模型、不执行工具。
    Raises:
        ValueError: 消息形状、调用身份或顺序不合法。
    """
    if not isinstance(messages, list) or not messages or len(messages) > 30:
        raise ValueError("消息需要1至30项")
    pending: set[str] = set()
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in {
            "system",
            "user",
            "assistant",
            "tool",
        }:
            raise ValueError("未支持的消息角色")
        role = message["role"]
        if message.get("content") is not None and not isinstance(message["content"], str):
            raise ValueError("本课原生适配只处理文本")
        if role == "tool":
            identity = message.get("tool_call_id")
            if identity not in pending:
                raise ValueError("工具回执没有当前配对申请")
            pending.remove(identity)
        else:
            if pending:
                raise ValueError("申请尚未得到回执，不能进入下一轮")
            calls = message.get("tool_calls", [])
            if calls and role != "assistant":
                raise ValueError("只有assistant可以申请工具")
            for call in calls:
                identity = call.get("id")
                function = call.get("function", {})
                if not identity or identity in pending or call.get("type") != "function":
                    raise ValueError("工具申请身份或类型不合法")
                if not function.get("name") or not isinstance(function.get("arguments"), str):
                    raise ValueError("工具申请缺少名称或JSON参数文本")
                json.loads(function["arguments"])
                pending.add(identity)
    if pending:
        raise ValueError("工具回执尚不齐全")


class NativeGateway:
    """只重用当前配置，每个实例有限调用；凭据不返回或显示。"""

    def __init__(self, model: Any, max_calls: int = 4) -> None:
        if type(model).__name__ != "ChatDeepSeek" or type(max_calls) is not int or max_calls < 1:
            raise ValueError("原生演示仅核对当前DeepSeek适配器和正整数预算")
        base = getattr(model, "api_base", None) or getattr(model, "openai_api_base", None)
        key = getattr(model, "api_key", None) or getattr(model, "openai_api_key", None)
        parsed = urlparse(str(base))
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query:
            raise ValueError("原生地址必须是当前HTTPS配置且不含凭据或query")
        if not key or not hasattr(key, "get_secret_value"):
            raise ValueError("当前模型没有可安全重用的凭据对象")
        self._key = key.get_secret_value()
        self._url = str(base).rstrip("/") + "/chat/completions"
        self.model_id = str(model.model_name)
        self._options = {
            name: getattr(model, name)
            for name in ("temperature", "max_tokens")
            if getattr(model, name, None) is not None
        }
        self._extra = copy.deepcopy(getattr(model, "extra_body", None) or {})
        if getattr(model, "model_kwargs", None):
            raise ValueError("当前非默认model_kwargs需先扩展原生接口契约，不静默丢弃参数")
        self.calls, self.max_calls = 0, max_calls

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> dict[str, Any]:
        """异步执行一次当前原生请求，保留公开字段。

        Args:
            messages: 原生文本消息；tools: 已公开schema；transport: 仅单测故障替身。
        Returns:
            assistant公开正文/动作与总token数；不含隐藏推理、原始响应或请求头。
        Raises:
            ValueError: 协议或能力不支持；RuntimeError: 调用耗尽。
            TimeoutError: 20秒；HTTP与解析错误原样保留。
        """
        validate_wire_messages(messages)
        if tools and self._extra.get("thinking", {}).get("type") != "disabled":
            raise ValueError("工具对照只验证当前非思考模式，不擅自改配置或转存隐藏推理")
        if self.calls >= self.max_calls:
            raise RuntimeError("原生调用预算耗尽")
        self.calls += 1
        payload = {
            "model": self.model_id,
            "messages": copy.deepcopy(messages),
            "stream": False,
            **self._options,
            **self._extra,
        }
        if tools:
            payload["tools"] = copy.deepcopy(tools)
        async with (
            asyncio.timeout(20),
            httpx.AsyncClient(timeout=20, transport=transport) as client,
        ):
            response = await client.post(
                self._url, headers={"Authorization": "Bearer " + self._key}, json=payload
            )
            response.raise_for_status()
            packet = response.json()
        raw = packet["choices"][0]["message"]
        message = {"role": "assistant", "content": raw.get("content") or ""}
        if raw.get("tool_calls"):
            message["tool_calls"] = raw["tool_calls"]
        usage = packet.get("usage", {})
        return {
            "message": message,
            "model": self.model_id,
            "calls": self.calls,
            "usage": {
                key: usage.get(key)
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
            },
        }
