from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

from src import agent


def _response(output: list[object], output_text: str = "", status: str = "completed") -> SimpleNamespace:
    return SimpleNamespace(output=output, output_text=output_text, status=status)


def test_responses_tool_schema_uses_responses_shape() -> None:
    schemas = agent._responses_tool_schemas()
    assert schemas
    assert all(schema["type"] == "function" for schema in schemas)
    assert all("name" in schema and "parameters" in schema for schema in schemas)
    assert all("function" not in schema for schema in schemas)
    assert all(schema["strict"] is False for schema in schemas)


def test_openai_tool_results_use_function_call_output_and_call_id() -> None:
    function_call = SimpleNamespace(
        type="function_call",
        name="calculate",
        arguments='{"expression":"1+2"}',
        call_id="call_abc123",
    )
    first = _response([function_call])
    second = _response(
        [SimpleNamespace(type="message", content=[])],
        output_text="計算結果は3です。",
    )
    fake_api = Mock()
    fake_api.responses.create.side_effect = [first, second]

    with patch.object(
        agent,
        "resolve_inference",
        return_value=(fake_api, "gpt-test", "openai"),
    ):
        answer = agent.ask("1+2を計算してください")

    assert "計算結果は3です" in answer
    assert fake_api.chat.completions.create.call_count == 0
    assert fake_api.responses.create.call_count == 2

    second_request = fake_api.responses.create.call_args_list[1].kwargs
    tool_output = [
        item for item in second_request["input"]
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    ]
    assert len(tool_output) == 1
    assert tool_output[0]["call_id"] == "call_abc123"
    assert tool_output[0]["output"] == "3"
    assert second_request["store"] is False
    assert "reasoning.encrypted_content" in second_request["include"]

    first_request = fake_api.responses.create.call_args_list[0].kwargs
    assert first_request["tools"][0]["type"] == "function"
    assert "name" in first_request["tools"][0]
    assert "function" not in first_request["tools"][0]


def test_openai_text_only_question_still_uses_responses() -> None:
    fake_api = Mock()
    fake_api.responses.create.return_value = _response(
        [SimpleNamespace(type="message", content=[])],
        output_text="こんにちは",
    )
    with patch.object(
        agent,
        "resolve_inference",
        return_value=(fake_api, "gpt-test", "openai"),
    ):
        assert agent.ask("こんにちは") == "こんにちは"
    fake_api.responses.create.assert_called_once()
    assert fake_api.chat.completions.create.call_count == 0


def test_gemini_stays_on_chat_completions() -> None:
    message = SimpleNamespace(content="Gemini応答", tool_calls=None)
    fake_api = Mock()
    fake_api.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )
    with patch.object(
        agent,
        "resolve_inference",
        return_value=(fake_api, "gemini-test", "gemini"),
    ):
        assert agent.ask("こんにちは") == "Gemini応答"
    fake_api.chat.completions.create.assert_called_once()
    assert fake_api.responses.create.call_count == 0


def test_responses_failure_status_returns_diagnostic() -> None:
    fake_api = Mock()
    fake_api.responses.create.return_value = _response(
        [], status="incomplete"
    )
    with patch.object(
        agent,
        "resolve_inference",
        return_value=(fake_api, "gpt-test", "openai"),
    ):
        answer = agent.ask("長い質問")
    assert "status=incomplete" in answer
