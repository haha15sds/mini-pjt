"""메시지 본문 꺼내기 (LangChain 메시지 객체와 직렬화된 dict 모두)."""
from __future__ import annotations


def text_of(msg) -> str:
    """메시지(객체 또는 dict)의 텍스트 본문. content가 블록 목록이면 text 블록만 이어 붙인다."""
    c = msg.get("content") if isinstance(msg, dict) else msg.content
    if isinstance(c, list):
        return "".join(b.get("text", "") for b in c if isinstance(b, dict))
    return str(c or "")
