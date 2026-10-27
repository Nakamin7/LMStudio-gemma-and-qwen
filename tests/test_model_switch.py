from unittest.mock import patch
import sys
import types
try:
    from openai import OpenAI
except ImportError:
    sys.modules["openai"] = types.SimpleNamespace(OpenAI=object)
from src import lmstudio


def test_switch_rejects_unknown_model():
    with patch.object(lmstudio, "local_models", return_value=[{"key": "installed", "type": "llm"}]):
        try:
            lmstudio.switch_model("unknown")
        except ValueError as exc:
            assert "登録されていない" in str(exc)
        else:
            raise AssertionError("Unknown model should fail")


def test_switch_loaded_model_reuses_instance():
    model = {"key": "gemma", "display_name": "Gemma", "loaded_instances": [{"id": "gemma-1"}]}
    with patch.object(lmstudio, "local_models", return_value=[model]), patch.object(lmstudio, "_save_model") as save, patch.object(lmstudio, "_rest_request") as req:
        output = lmstudio.switch_model("gemma")
        assert "gemma-1" in output
        save.assert_called_once_with("gemma-1")
        req.assert_not_called()


def test_switch_unloads_then_loads():
    models = [{"key": "old", "loaded_instances": [{"id": "old-instance"}]}, {"key": "new", "loaded_instances": []}]
    def api(path, payload):
        if path == "models/load":
            return {"status": "loaded", "instance_id": "new-instance"}
        return {"instance_id": "old-instance"}
    with patch.object(lmstudio, "local_models", return_value=models), patch.object(lmstudio, "_save_model") as save, patch.object(lmstudio, "_rest_request", side_effect=api) as req:
        lmstudio.switch_model("new")
        assert req.call_args_list[0].args[0] == "models/unload"
        assert req.call_args_list[1].args[0] == "models/load"
        assert save.call_args_list[-1].args == ("new-instance",)
