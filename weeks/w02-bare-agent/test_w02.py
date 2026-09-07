"""Week 02 的规格说明。

全部离线运行：模型用 FakeLLM 照剧本演，不联网、不花钱、结果确定。
"""

from __future__ import annotations

import ex1_messages as ex1
import ex2_tool_registry as ex2
import ex3_agent_loop as ex3
import pytest


class TestConversation:
    def test_system_prompt_goes_first_and_is_optional(self) -> None:
        assert ex1.Conversation("规矩").messages == [{"role": "system", "content": "规矩"}]
        assert ex1.Conversation().messages == []

    def test_each_conversation_has_its_own_history(self) -> None:
        # 可变默认参数的坑：两段对话必须互不干扰。
        a, b = ex1.Conversation(), ex1.Conversation()
        a.add_user("只加到 a")
        assert b.messages == []

    def test_assistant_without_tool_calls_omits_the_key(self) -> None:
        conv = ex1.Conversation()
        conv.add_assistant("纯文本回复")
        assert conv.messages[-1] == {"role": "assistant", "content": "纯文本回复"}

    def test_empty_tool_calls_also_omits_the_key(self) -> None:
        conv = ex1.Conversation()
        conv.add_assistant("回复", [])
        assert "tool_calls" not in conv.messages[-1]

    def test_assistant_with_tool_calls_keeps_them(self) -> None:
        conv = ex1.Conversation()
        calls = [{"id": "c1", "name": "f", "arguments": "{}"}]
        conv.add_assistant(None, calls)
        assert conv.messages[-1]["tool_calls"] == calls
        assert conv.messages[-1]["content"] is None

    def test_tool_result_carries_the_matching_call_id(self) -> None:
        conv = ex1.Conversation()
        conv.add_tool_result("c1", "晴，25 度")
        assert conv.messages[-1] == {
            "role": "tool",
            "content": "晴，25 度",
            "tool_call_id": "c1",
        }

    def test_api_format_is_a_copy(self) -> None:
        # 调用方改返回值不能污染历史。
        conv = ex1.Conversation()
        conv.add_user("hi")
        exported = conv.to_api_format()
        exported.append({"role": "user", "content": "偷偷加的"})
        assert len(conv.messages) == 1

    def test_last_assistant_content_scans_backwards(self) -> None:
        conv = ex1.Conversation()
        conv.add_assistant("第一次回答")
        conv.add_user("再问")
        conv.add_assistant("第二次回答")
        assert conv.last_assistant_content() == "第二次回答"

    def test_last_assistant_content_is_none_when_absent(self) -> None:
        conv = ex1.Conversation("规矩")
        conv.add_user("hi")
        assert conv.last_assistant_content() is None


class TestToolRegistry:
    def _registry(self) -> ex2.ToolRegistry:
        registry = ex2.ToolRegistry()
        registry.register(ex2.get_weather)
        registry.register(ex2.calculator)
        return registry

    def test_registering_an_undecorated_function_fails_loudly(self) -> None:
        def plain(x: int) -> int:
            return x

        with pytest.raises(ValueError, match="plain"):
            ex2.ToolRegistry().register(plain)

    def test_schemas_carry_name_description_and_parameters(self) -> None:
        schemas = {s["name"]: s for s in self._registry().to_schemas()}
        assert set(schemas) == {"get_weather", "calculator"}
        assert schemas["get_weather"]["description"] == "查询指定城市的当前天气。"
        assert schemas["get_weather"]["parameters"]["required"] == ["city"]

    def test_empty_registry_exports_nothing(self) -> None:
        assert ex2.ToolRegistry().to_schemas() == []

    def test_successful_call_returns_the_result_as_text(self) -> None:
        assert self._registry().call("get_weather", '{"city": "上海"}') == "晴，25 度"

    def test_unknown_tool_names_the_available_ones(self) -> None:
        # 模型看到可用工具列表，下一轮就能自己改对。
        result = self._registry().call("get_wether", '{"city": "上海"}')
        assert "get_weather" in result
        assert "calculator" in result

    def test_malformed_arguments_return_an_error_not_a_crash(self) -> None:
        result = self._registry().call("get_weather", "{坏掉的")
        assert isinstance(result, str)
        assert "{坏掉的" in result

    def test_tool_raising_is_reported_not_propagated(self) -> None:
        result = self._registry().call("get_weather", '{"city": "火星"}')
        assert isinstance(result, str)
        assert "火星" in result


class TestAgentLoop:
    def _registry(self) -> ex2.ToolRegistry:
        registry = ex2.ToolRegistry()
        registry.register(ex2.get_weather)
        registry.register(ex2.calculator)
        return registry

    async def test_answer_without_tools_returns_immediately(self) -> None:
        llm = ex3.FakeLLM([{"content": "你好", "tool_calls": []}])
        agent = ex3.Agent(llm, self._registry())

        assert await agent.run(ex1.Conversation(), "在吗") == "你好"
        assert len(llm.seen_messages) == 1, "不需要工具时只该问模型一次"

    async def test_tool_result_is_fed_back_and_loop_continues(self) -> None:
        llm = ex3.FakeLLM(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": '{"city": "上海"}'}
                    ],
                },
                {"content": "上海晴，25 度。", "tool_calls": []},
            ]
        )
        conv = ex1.Conversation()
        agent = ex3.Agent(llm, self._registry())

        assert await agent.run(conv, "上海天气") == "上海晴，25 度。"
        assert [m["role"] for m in conv.messages] == ["user", "assistant", "tool", "assistant"]
        assert conv.messages[2]["content"] == "晴，25 度"
        assert conv.messages[2]["tool_call_id"] == "c1"

    async def test_second_request_sees_the_tool_result(self) -> None:
        # 模型不记得任何事，全靠你把历史发回去。
        llm = ex3.FakeLLM(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": '{"city": "北京"}'}
                    ],
                },
                {"content": "北京多云。", "tool_calls": []},
            ]
        )
        await ex3.Agent(llm, self._registry()).run(ex1.Conversation(), "北京天气")

        second_request = llm.seen_messages[1]
        assert any(m["role"] == "tool" for m in second_request)

    async def test_multiple_tool_calls_in_one_turn(self) -> None:
        llm = ex3.FakeLLM(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": '{"city": "上海"}'},
                        {"id": "c2", "name": "calculator", "arguments": '{"expression": "2+3"}'},
                    ],
                },
                {"content": "都查好了。", "tool_calls": []},
            ]
        )
        conv = ex1.Conversation()
        await ex3.Agent(llm, self._registry()).run(conv, "查两件事")

        tool_messages = [m for m in conv.messages if m["role"] == "tool"]
        assert len(tool_messages) == 2, "一轮里的每个 tool_call 都要有自己的 tool 消息"
        assert [m["tool_call_id"] for m in tool_messages] == ["c1", "c2"]

    async def test_failing_tool_does_not_break_the_loop(self) -> None:
        llm = ex3.FakeLLM(
            [
                {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "name": "get_weather", "arguments": '{"city": "火星"}'}
                    ],
                },
                {"content": "那个城市查不到。", "tool_calls": []},
            ]
        )
        conv = ex1.Conversation()

        # 工具抛异常也不该中断 agent：错误变成 tool 消息，模型自己决定怎么办。
        assert await ex3.Agent(llm, self._registry()).run(conv, "火星天气") == "那个城市查不到。"
        assert "火星" in conv.messages[2]["content"]

    async def test_iteration_cap_stops_an_endless_loop(self) -> None:
        # 模型每轮都要求调工具，永不给答案。护栏必须拦住它。
        forever = {
            "content": None,
            "tool_calls": [{"id": "c", "name": "get_weather", "arguments": '{"city": "上海"}'}],
        }
        llm = ex3.FakeLLM([forever] * 10)
        agent = ex3.Agent(llm, self._registry(), max_iterations=3)

        result = await agent.run(ex1.Conversation(), "绕圈子")

        assert "3" in result, "撞上限时的说明里要带上 max_iterations 的值"
        assert len(llm.seen_messages) == 3, "不能超过 max_iterations 次模型调用"
