"""Deterministic source-provenance checks for RAG answers."""
import re

def verify_answer_citations(answer: str, retrieved_sources: list[str]) -> str:
    """Deterministically check that cited source names came from retrieved evidence.

    This validates citation provenance, not the truth of every natural-language claim.
    """
    answer = str(answer or '')
    allowed = {str(s).strip().casefold() for s in retrieved_sources if str(s).strip()}
    citations = re.findall(r"\[出典:\s*([^\]]+)\]", answer)
    unsupported = [c.strip() for c in citations if c.strip().casefold() not in allowed]
    if unsupported:
        answer += "\n\n[根拠検証の警告] 検索結果に含まれない出典名が引用されています: " + ", ".join(unsupported)
    elif retrieved_sources and not citations:
        answer += "\n\n[根拠検証の注意] ナレッジ検索は実行されましたが、回答に出典引用がありません。回答内容と資料の対応を確認してください。"
    return answer

