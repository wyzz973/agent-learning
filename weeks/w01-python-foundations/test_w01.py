"""Week 01 的规格说明。

每条测试描述一个必须成立的行为。函数体由我实现，红变绿即本周完成。
测试全部离线运行，不请求外网。
"""

from __future__ import annotations

import asyncio
import time

import ex1_async_basics as ex1
import ex2_retry as ex2
import ex3_tool_schema as ex3
import ex4_tool_decorator as ex4
import ex5_settings as ex5
import pytest


class TestAsyncBasics:
    async def test_sequential_preserves_order(self) -> None:
        assert await ex1.run_sequential([1, 2, 3]) == [2, 4, 6]

    async def test_concurrent_preserves_input_order(self) -> None:
        # gather 按入参顺序返回，不按完成顺序。拼装工具结果时依赖这一点。
        assert await ex1.run_concurrent([1, 2, 3]) == [2, 4, 6]

    async def test_concurrent_is_much_faster_than_sequential(self) -> None:
        values = list(range(6))

        start = time.perf_counter()
        await ex1.run_sequential(values)
        sequential = time.perf_counter() - start

        start = time.perf_counter()
        await ex1.run_concurrent(values)
        concurrent = time.perf_counter() - start

        assert concurrent < sequential / 3

    async def test_limited_concurrency_never_exceeds_limit(self, monkeypatch) -> None:
        in_flight = 0
        peak = 0

        async def counting_double(x: int, delay: float = 0.05) -> int:
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(delay)
            in_flight -= 1
            return x * 2

        monkeypatch.setattr(ex1, "slow_double", counting_double)
        result = await ex1.run_concurrent_limited(list(range(9)), 3)

        assert peak <= 3, f"同时在飞 {peak} 个，超过了 limit=3"
        assert result == [x * 2 for x in range(9)]


class TestRetry:
    async def test_returns_immediately_on_success(self) -> None:
        calls = 0

        async def succeed() -> str:
            nonlocal calls
            calls += 1
            return "ok"

        assert await ex2.with_retry(succeed, attempts=3) == "ok"
        assert calls == 1, "成功后不该再重试"

    async def test_retries_until_success(self) -> None:
        calls = 0

        async def fail_twice() -> str:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise ConnectionError("boom")
            return "ok"

        assert await ex2.with_retry(fail_twice, attempts=5, backoff=0.0) == "ok"
        assert calls == 3

    async def test_raises_retry_exhausted_carrying_last_error(self) -> None:
        async def always_fail() -> str:
            raise ConnectionError("still broken")

        with pytest.raises(ex2.RetryExhausted) as exc_info:
            await ex2.with_retry(always_fail, attempts=3, backoff=0.0)

        assert exc_info.value.attempts == 3
        assert isinstance(exc_info.value.last_error, ConnectionError)

    async def test_does_not_retry_unlisted_exceptions(self) -> None:
        # 参数错误重试多少次都不会好，只会浪费时间和钱。
        calls = 0

        async def bad_argument() -> str:
            nonlocal calls
            calls += 1
            raise ValueError("wrong argument")

        with pytest.raises(ValueError):
            await ex2.with_retry(bad_argument, attempts=3, backoff=0.0)
        assert calls == 1, "不在 retry_on 里的异常必须直接抛出"

    async def test_timeout_counts_as_a_failed_attempt(self) -> None:
        async def too_slow() -> str:
            await asyncio.sleep(1.0)
            return "never"

        with pytest.raises(ex2.RetryExhausted):
            await ex2.with_retry(too_slow, attempts=2, timeout=0.05, backoff=0.0)

    async def test_backoff_grows_between_attempts(self) -> None:
        async def always_fail() -> str:
            raise ConnectionError("boom")

        start = time.perf_counter()
        with pytest.raises(ex2.RetryExhausted):
            await ex2.with_retry(always_fail, attempts=3, backoff=0.05)
        elapsed = time.perf_counter() - start

        # 两次退避：0.05 + 0.10 = 0.15；最后一次失败后不该再睡。
        assert 0.13 < elapsed < 0.30, f"退避总时长 {elapsed:.3f}s 不符合指数退避"


class TestToolSchema:
    def test_schema_has_the_three_fields_a_provider_expects(self) -> None:
        schema = ex3.build_tool_schema(ex3.WeatherQuery, "get_weather", "查天气")
        assert schema["name"] == "get_weather"
        assert schema["description"] == "查天气"
        assert schema["input_schema"]["type"] == "object"

    def test_nested_model_becomes_a_defs_reference(self) -> None:
        schema = ex3.build_tool_schema(ex3.WeatherQuery, "get_weather", "查天气")
        assert "$defs" in schema["input_schema"], "嵌套模型应出现在 $defs 里"
        assert "Location" in schema["input_schema"]["$defs"]

    def test_literal_field_becomes_an_enum(self) -> None:
        schema = ex3.build_tool_schema(ex3.WeatherQuery, "get_weather", "查天气")
        unit = schema["input_schema"]["properties"]["unit"]
        assert unit.get("enum") == ["celsius", "fahrenheit"]

    def test_every_field_carries_a_description_for_the_model(self) -> None:
        # 字段描述是给模型的 prompt。缺了描述，模型只能靠字段名猜。
        properties = ex3.build_tool_schema(ex3.WeatherQuery, "w", "d")["input_schema"]["properties"]
        missing = [name for name, spec in properties.items() if not spec.get("description")]
        assert not missing, f"这些字段缺 description: {missing}"

    def test_defaulted_fields_are_not_required(self) -> None:
        schema = ex3.build_tool_schema(ex3.WeatherQuery, "w", "d")
        assert ex3.describe_required_fields(schema["input_schema"]) == ["location"]


class TestToolDecorator:
    def test_decorated_function_still_works_normally(self) -> None:
        assert ex4.add(2, 3) == 5
        assert ex4.search("x", 2) == ["x-0", "x-1"]

    def test_metadata_is_attached(self) -> None:
        meta = ex4.add.__tool__
        assert meta["name"] == "add"
        assert meta["description"] == "把两个整数相加。"
        assert meta["parameters"] == {"a": "int", "b": "int"}

    def test_description_takes_only_the_first_docstring_line(self) -> None:
        assert "\n" not in ex4.add.__tool__["description"]

    def test_wraps_preserves_identity(self) -> None:
        # 没有 functools.wraps 的话，调试时看到的全是 wrapper。
        assert ex4.add.__name__ == "add"
        assert ex4.add.__doc__ is not None

    def test_collect_tools_finds_every_decorated_function(self) -> None:
        names = {meta["name"] for meta in ex4.collect_tools(vars(ex4))}
        assert names == {"add", "search"}


class TestSettings:
    def test_loads_from_env_file(self, tmp_path, monkeypatch) -> None:
        for key in ("DEFAULT_MODEL", "MAX_AGENT_ITERATIONS", "LANGSMITH_TRACING"):
            monkeypatch.delenv(key, raising=False)
        env = tmp_path / ".env"
        env.write_text("DEFAULT_MODEL=deepseek:deepseek-chat\nMAX_AGENT_ITERATIONS=5\n")

        settings = ex5.load_settings(env)

        assert settings.default_model == "deepseek:deepseek-chat"
        assert settings.max_agent_iterations == 5
        assert settings.llm_timeout_seconds == 60.0

    def test_existing_environment_wins_over_the_file(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setenv("DEFAULT_MODEL", "anthropic:claude-opus-5")
        env = tmp_path / ".env"
        env.write_text("DEFAULT_MODEL=deepseek:deepseek-chat\n")

        assert ex5.load_settings(env).default_model == "anthropic:claude-opus-5"

    def test_missing_required_setting_fails_loudly_and_names_the_variable(
        self, tmp_path, monkeypatch
    ) -> None:
        monkeypatch.delenv("DEFAULT_MODEL", raising=False)
        env = tmp_path / ".env"
        env.write_text("MAX_AGENT_ITERATIONS=5\n")

        with pytest.raises(Exception, match="DEFAULT_MODEL"):
            ex5.load_settings(env)

    def test_resolve_model_splits_provider_and_name(self) -> None:
        settings = ex5.Settings(default_model="deepseek:deepseek-chat")
        assert ex5.resolve_model(settings) == ("deepseek", "deepseek-chat")

    @pytest.mark.parametrize("bad", ["deepseek-chat", "a:b:c", ""])
    def test_resolve_model_rejects_malformed_values(self, bad: str) -> None:
        settings = ex5.Settings(default_model=bad)
        with pytest.raises(ValueError, match=bad if bad else "."):
            ex5.resolve_model(settings)
