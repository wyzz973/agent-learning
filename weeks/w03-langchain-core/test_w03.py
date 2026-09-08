"""Week 03 的规格说明。

全部离线：模型用 ScriptedChatModel 照剧本演，不联网、不花钱、结果确定。
"""

from __future__ import annotations

import ex1_messages as ex1
import ex2_tools as ex2
import ex3_create_agent as ex3
import pytest
from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage


def _call(name: str, args: dict[str, object], call_id: str = "c1") -> dict[str, object]:
    """造一个 LangChain 格式的 tool_call。"""
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


class TestMessages:
    def test_extract_tool_calls_flattens_every_ai_message(self) -> None:
        messages: list[AnyMessage] = [
            HumanMessage("查两个城市"),
            AIMessage(content="", tool_calls=[_call("get_weather", {"city": "上海"}, "c1")]),
            ToolMessage(content="晴", tool_call_id="c1"),
            AIMessage(content="", tool_calls=[_call("get_weather", {"city": "北京"}, "c2")]),
        ]
        assert ex1.extract_tool_calls(messages) == [
            {"name": "get_weather", "args": {"city": "上海"}},
            {"name": "get_weather", "args": {"city": "北京"}},
        ]

    def test_extract_tool_calls_is_empty_without_calls(self) -> None:
        assert ex1.extract_tool_calls([HumanMessage("你好"), AIMessage("你好呀")]) == []

    def test_from_dicts_maps_all_four_roles(self) -> None:
        raw = [
            {"role": "system", "content": "你是助手。"},
            {"role": "user", "content": "上海天气？"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "c1", "name": "get_weather", "arguments": '{"city": "上海"}'}
                ],
            },
            {"role": "tool", "content": "晴，25 度", "tool_call_id": "c1"},
        ]
        converted = ex1.from_dicts(raw)

        assert [type(m).__name__ for m in converted] == [
            "SystemMessage",
            "HumanMessage",
            "AIMessage",
            "ToolMessage",
        ]

    def test_from_dicts_parses_arguments_into_a_dict(self) -> None:
        # w02 的 arguments 是 JSON 字符串，LangChain 的 args 是字典。
        raw = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "c1", "name": "get_weather", "arguments": '{"city": "上海"}'}
                ],
            }
        ]
        assert ex1.from_dicts(raw)[0].tool_calls[0]["args"] == {"city": "上海"}

    def test_from_dicts_keeps_the_tool_call_id(self) -> None:
        raw = [{"role": "tool", "content": "晴", "tool_call_id": "c1"}]
        assert ex1.from_dicts(raw)[0].tool_call_id == "c1"

    def test_from_dicts_rejects_an_unknown_role(self) -> None:
        with pytest.raises(ValueError, match="assistent"):
            ex1.from_dicts([{"role": "assistent", "content": "拼错了"}])


class TestTools:
    def test_calculator_formats_to_the_requested_precision(self) -> None:
        assert ex2.calculator.invoke({"expression": "10 / 4", "precision": 3}) == "2.500"

    def test_calculator_defaults_to_two_decimals(self) -> None:
        assert ex2.calculator.invoke({"expression": "23 * 17"}) == "391.00"

    def test_calculator_rejects_dangerous_characters(self) -> None:
        with pytest.raises(ValueError, match="import"):
            ex2.calculator.invoke({"expression": "__import__('os')"})

    def test_calculator_reports_the_expression_when_evaluation_fails(self) -> None:
        # 错误信息要带上原表达式，否则排查时不知道是哪次调用出的问题。
        with pytest.raises(ValueError, match="1 / 0"):
            ex2.calculator.invoke({"expression": "1 / 0"})

    def test_tool_index_is_keyed_by_name(self) -> None:
        index = ex2.build_tool_index([ex2.get_weather, ex2.calculator])
        assert set(index) == {"get_weather", "calculator"}
        assert index["get_weather"] is ex2.get_weather

    def test_duplicate_tool_names_fail_loudly(self) -> None:
        # 静默覆盖的后果是模型调 A 实际执行了 B，极难排查。
        with pytest.raises(ValueError, match="get_weather"):
            ex2.build_tool_index([ex2.get_weather, ex2.get_weather])


class TestCreateAgent:
    def test_answer_without_tools(self) -> None:
        agent = ex3.build_agent([ex2.get_weather], ex3.scripted(AIMessage("你好呀")))
        assert ex3.run_agent(agent, "在吗") == "你好呀"

    def test_tool_result_feeds_back_into_the_next_turn(self) -> None:
        agent = ex3.build_agent(
            [ex2.get_weather],
            ex3.scripted(
                AIMessage(content="", tool_calls=[_call("get_weather", {"city": "上海"})]),
                AIMessage("上海今天晴，25 度。"),
            ),
        )
        assert ex3.run_agent(agent, "上海天气") == "上海今天晴，25 度。"

    def test_system_prompt_becomes_the_first_message(self) -> None:
        agent = ex3.build_agent(
            [ex2.get_weather], ex3.scripted(AIMessage("好的")), system_prompt="你是助手。"
        )
        result = agent.invoke({"messages": [HumanMessage("hi")]})
        assert isinstance(result["messages"][0], SystemMessage)

    def test_trace_records_every_step_in_order(self) -> None:
        agent = ex3.build_agent(
            [ex2.get_weather],
            ex3.scripted(
                AIMessage(content="", tool_calls=[_call("get_weather", {"city": "上海"})]),
                AIMessage("上海今天晴，25 度。"),
            ),
        )
        result = agent.invoke({"messages": [HumanMessage("上海天气？")]})
        trace = ex3.trace_of(result)

        assert len(trace) == 4
        assert trace[0].startswith("human")
        assert "get_weather" in trace[1]
        assert trace[2].startswith("tool")
        assert "晴" in trace[3]

    def test_plain_agent_lets_a_tool_error_escape(self) -> None:
        # create_agent 默认不接住工具异常——这一点上你 w02 手写的版本更健壮。
        agent = ex3.build_agent(
            [ex2.get_weather],
            ex3.scripted(
                AIMessage(content="", tool_calls=[_call("get_weather", {"city": "火星"})]),
                AIMessage("查不到火星的天气。"),
            ),
        )
        with pytest.raises(ValueError, match="火星"):
            agent.invoke({"messages": [HumanMessage("火星天气？")]})

    def test_resilient_agent_turns_the_error_into_a_tool_message(self) -> None:
        # 加上 ToolErrorMiddleware 才恢复你 w02 手写的那个行为。
        agent = ex3.build_resilient_agent(
            [ex2.get_weather],
            ex3.scripted(
                AIMessage(content="", tool_calls=[_call("get_weather", {"city": "火星"})]),
                AIMessage("查不到火星的天气。"),
            ),
        )
        result = agent.invoke({"messages": [HumanMessage("火星天气？")]})

        tool_messages = [m for m in result["messages"] if m.type == "tool"]
        assert len(tool_messages) == 1
        assert "火星" in tool_messages[0].text, "错误信息要带上原因，模型才能自己改对"
        assert result["messages"][-1].text == "查不到火星的天气。"
