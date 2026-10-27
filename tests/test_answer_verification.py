from src.evidence import verify_answer_citations


def test_verifier_flags_unsupported_citations():
    text = verify_answer_citations('回答です [出典: evil.md]', ['good.md'])
    assert '根拠検証の警告' in text


def test_verifier_warns_when_search_used_but_no_citation():
    text = verify_answer_citations('回答です', ['good.md'])
    assert '根拠検証の注意' in text


def test_verifier_accepts_retrieved_citation():
    text = verify_answer_citations('回答です [出典: good.md]', ['good.md'])
    assert '根拠検証の警告' not in text
