import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src import providers


def test_default_local_and_persistence(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    assert providers.current_provider() == 'local'
    with patch.object(providers.lmstudio, '_saved_model', return_value='local-instance'):
        assert providers.current_selection() == ('local', 'local-instance')
    monkeypatch.setenv('OPENAI_API_KEY', 'sk-example-test')
    providers.set_provider('openai', 'gpt-4.1-mini', cloud_confirmed=True)
    assert providers.current_selection() == ('openai', 'gpt-4.1-mini')
    # Local preferences remain separate from the cloud model preference.
    providers.set_provider('local')
    assert providers.current_provider() == 'local'
    providers.set_provider('openai', 'gpt-4.1-mini', cloud_confirmed=True)
    assert providers.current_provider() == 'openai'
    assert 'sk-example-test' not in (tmp_path / 'provider.sqlite3').read_bytes().decode('latin-1')


def test_requires_consent_and_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    try:
        providers.set_provider('openai', 'gpt-4.1-mini', cloud_confirmed=True)
    except RuntimeError as exc:
        assert 'OPENAI_API_KEY' in str(exc)
    else:
        assert False, 'Cloud key is required'
    monkeypatch.setenv('OPENAI_API_KEY', 'test-only-key')
    try:
        providers.set_provider('openai', 'gpt-4.1-mini', cloud_confirmed=False)
    except ValueError:
        pass
    else:
        assert False, 'Cloud consent is required'
    assert providers.current_provider() == 'local'


def test_resolve_provider_clients(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-openai')
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-gemini')
    with patch.object(providers, 'OpenAI', return_value='cloud-client') as sdk:
        providers.set_provider('openai', 'gpt-4.1-mini', True)
        assert providers.resolve_inference() == ('cloud-client', 'gpt-4.1-mini', 'openai')
        assert sdk.call_args.kwargs['api_key'] == 'fake-openai'
        assert 'base_url' not in sdk.call_args.kwargs

        providers.set_provider('gemini', 'gemini-2.5-flash', True)
        assert providers.resolve_inference() == ('cloud-client', 'gemini-2.5-flash', 'gemini')
        assert sdk.call_args.kwargs['base_url'] == providers.GEMINI_URL

    providers.set_provider('local')
    with patch.object(providers.lmstudio, 'client', return_value='local-client'), patch.object(
        providers.lmstudio, 'selected_model', return_value='gemma-instance'
    ):
        assert providers.resolve_inference() == ('local-client', 'gemma-instance', 'local')


def test_provider_model_listing(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-gemini')
    class FakeResponse:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return b'{"models":[{"name":"models/gemini-test","baseModelId":"gemini-test","supportedGenerationMethods":["generateContent"]},{"name":"models/text-embedding-test","baseModelId":"text-embedding-test","supportedGenerationMethods":["embedContent"]}]}'
    with patch.object(providers, 'urlopen', return_value=FakeResponse()) as request:
        assert providers.list_provider_models('gemini') == ['gemini-test']
        req = request.call_args.args[0]
        assert req.get_header('X-goog-api-key') == 'fake-gemini'
        assert 'fake-gemini' not in req.full_url


def test_gemini_api_error_is_actionable(monkeypatch):
    from urllib.error import HTTPError
    import io
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-gemini')
    error = HTTPError('https://example.invalid', 403, 'Forbidden', {}, io.BytesIO(b'{"error":{"status":"PERMISSION_DENIED","message":"API key not valid"}}'))
    with patch.object(providers, 'urlopen', side_effect=error):
        try:
            providers.list_provider_models('gemini')
        except RuntimeError as exc:
            assert 'HTTP 403' in str(exc)
            assert 'PERMISSION_DENIED' in str(exc)
        else:
            assert False, 'Expected detailed Google API error'


def test_invalid_input(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-openai')
    for model in ('', '../../secret', 'evil\nmodel', 'a' * 129):
        try:
            providers.set_provider('openai', model, True)
        except ValueError:
            pass
        else:
            assert False, f'bad model: {model}'
    try:
        providers.set_provider('other', 'model', True)
    except ValueError:
        pass
    else:
        assert False


def test_agent_uses_selected_cloud_model(monkeypatch):
    from src import agent
    message = SimpleNamespace(content='こんにちは', tool_calls=None)
    fake_api = Mock()
    fake_api.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=message)]
    )
    with patch.object(agent, 'resolve_inference', return_value=(fake_api, 'gpt-test', 'openai')):
        assert agent.ask('こんにちは') == 'こんにちは'
    assert fake_api.chat.completions.create.call_args.kwargs['model'] == 'gpt-test'
    assert fake_api.chat.completions.create.call_args.kwargs['tool_choice'] == 'auto'


def test_no_automatic_cloud_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setenv('GEMINI_API_KEY', 'test-gemini')
    with patch.object(providers.lmstudio, 'selected_model', side_effect=RuntimeError('LM Studio offline')):
        with patch.object(providers.lmstudio, 'client', return_value='local-client'):
            try:
                providers.resolve_inference()
            except RuntimeError as exc:
                assert 'LM Studio offline' in str(exc)
            else:
                assert False, 'Must fail local-only, not silently move to cloud'

def test_model_ids_separate_per_cloud_provider(tmp_path, monkeypatch):
    monkeypatch.setattr(providers, 'PREF_DB', tmp_path / 'provider.sqlite3')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-openai')
    monkeypatch.setenv('GEMINI_API_KEY', 'test-gemini')
    providers.set_provider('openai', 'gpt-4.1-mini', True)
    providers.set_provider('gemini', 'gemini-2.5-flash', True)
    providers.set_provider('openai', 'gpt-4.1-mini', True)
    assert providers.current_selection() == ('openai', 'gpt-4.1-mini')
    providers.set_provider('gemini', 'gemini-2.5-flash', True)
    assert providers.current_selection() == ('gemini', 'gemini-2.5-flash')
