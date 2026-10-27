from types import SimpleNamespace
from unittest.mock import Mock, patch

from src import agent


def test_gemini_tool_call_extra_content_is_preserved(monkeypatch):
    signature = "test-signature"
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="list_workspace_files", arguments="{}"),
        model_dump=lambda **kwargs: {
            "id": "call_1",
            "type": "function",
            "function": {"name": "list_workspace_files", "arguments": "{}"},
            "extra_content": {"google": {"thought_signature": signature}},
        },
    )
    first_message = SimpleNamespace(content=None, tool_calls=[tool_call])
    final_message = SimpleNamespace(content="完了", tool_calls=None)
    fake_api = Mock()
    fake_api.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=first_message)]),
        SimpleNamespace(choices=[SimpleNamespace(message=final_message)]),
    ]

    with patch.object(agent, "resolve_inference", return_value=(fake_api, "gemini-test", "gemini")):
        assert agent.ask("ファイル一覧を確認して") == "完了"

    second_request_messages = fake_api.chat.completions.create.call_args_list[1].kwargs["messages"]
    assistant_tool_message = next(
        message for message in second_request_messages
        if message.get("role") == "assistant" and message.get("tool_calls")
    )
    assert assistant_tool_message["tool_calls"][0]["extra_content"]["google"]["thought_signature"] == signature
