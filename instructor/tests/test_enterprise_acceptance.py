"""检查验收设施的观察边界，替身只用于设施测试，绝不记为本人业务验收。"""

from typing import Any

import pytest

from instructor.enterprise_acceptance import ModelProbe, observe, prepare


@pytest.mark.asyncio
async def test_claimed_answer_without_real_input_cannot_pass_current_version_case() -> None:
    env = await prepare("M01", "contract_current", None, "阿灯本次岗位")
    record = observe(env, {"status": "answered"}, "answered", [])
    assert record["checks"]["returned_target_status"] is True
    assert record["checks"]["current_text_in_actual_model_input"] is False
    assert record["narrow_checks_passed"] is False


@pytest.mark.asyncio
async def test_claimed_retry_without_transaction_cannot_pass() -> None:
    env = await prepare("M02", "repeat_request", None, "阿灯本次岗位")
    assert env.facts["approved"] is True
    assert env.service.publication_count() == 0
    record = observe(env, {"status": "reported"}, "reported", [])
    assert record["checks"]["one_committed_publication"] is False
    assert record["narrow_checks_passed"] is False


@pytest.mark.asyncio
async def test_target_not_delivered_to_candidate_and_cases_have_independent_state() -> None:
    first = await prepare("M04", "withdrawn_latest", None, "阿灯本次岗位")
    second = await prepare("M04", "concurrent_update", None, "阿灯本次岗位")
    assert "target_status" not in first.facts and "expected_answer" not in first.facts
    assert first.run_dir != second.run_dir
    assert first.service.current_preference(first.principal, "style", 20) is None
    current = second.service.current_preference(second.principal, "style", 20)
    assert current and current["version"] == 2


@pytest.mark.asyncio
async def test_model_probe_never_adds_hidden_context_and_adapters_share_budget() -> None:
    class FakeModel:
        async def ainvoke(self, messages: list[Any], **kwargs: Any) -> list[Any]:
            return messages

        def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
            return self

    from langchain.messages import HumanMessage

    messages = [HumanMessage("只含我当前交付的文字")]
    probe = ModelProbe(FakeModel())
    assert await probe.ainvoke(messages) is messages
    derived = probe.with_structured_output(dict)
    await derived.ainvoke(messages)
    assert probe.ledger["calls"] == 2
    assert len(probe.ledger["inputs"][0]) == 1
    assert probe.ledger["inputs"][0][0]["content"] == "只含我当前交付的文字"
    probe.ledger["calls"] = 12
    with pytest.raises(RuntimeError, match="调用数"):
        await derived.ainvoke(messages)


@pytest.mark.asyncio
async def test_native_model_observer_is_compatible_with_create_agent() -> None:
    from langchain.agents import create_agent
    from langchain.messages import HumanMessage
    from langchain_core.language_models.fake_chat_models import FakeListChatModel

    fake = FakeListChatModel(responses=["设施替身结果"])
    env = await prepare("M01", "unknown_fact", fake, "阿灯本次岗位")
    app = create_agent(env.model, [], system_prompt="阿灯本次岗位")
    await app.ainvoke({"messages": [HumanMessage("设施参数验证")]})
    assert env.probe.ledger["calls"] == 1
    assert fake.callbacks is None
    assert env.model is not fake and isinstance(env.model, type(fake))
    env.probe.ledger["calls"] = 12
    with pytest.raises(RuntimeError, match="调用数"):
        await env.model.ainvoke([HumanMessage("设施预算验证")])


@pytest.mark.asyncio
async def test_list_retrieval_is_accepted_as_actual_versioned_read() -> None:
    import json

    from langchain.messages import HumanMessage

    env = await prepare("M05", "source_changed", None, "阿灯本次岗位")
    event_file = env.run_dir / "business-events.jsonl"
    before = len(event_file.read_text().splitlines())
    docs = env.service.visible_documents(env.principal)
    # 这里只验证grader的数据契约，record不冒充真实模型调用。
    env.probe.record([HumanMessage(json.dumps(docs, ensure_ascii=False))])
    events = [json.loads(line) for line in event_file.read_text().splitlines()[before:]]
    result = observe(env, {"status": "reported"}, "reported", events)
    assert result["checks"]["current_v2_read"] is True
    assert result["checks"]["current_text_in_actual_model_input"] is True


@pytest.mark.asyncio
async def test_withdrawal_consult_does_not_require_irrelevant_document_fetch() -> None:
    import json

    from langchain.messages import HumanMessage

    env = await prepare("M04", "withdrawn_latest", None, "阿灯本次岗位")
    event_file = env.run_dir / "business-events.jsonl"
    before = len(event_file.read_text().splitlines())
    assert env.service.current_preference(env.principal, "style", 20) is None
    env.probe.record([HumanMessage("林禾已经核对当前偏好不可使用，请自然告诉读者。")])
    events = [json.loads(line) for line in event_file.read_text().splitlines()[before:]]
    result = observe(env, {"status": "answered"}, "answered", events)
    assert result["checks"]["actual_current_memory_read"] is True
    assert "actual_grounded_request" not in result["checks"]
