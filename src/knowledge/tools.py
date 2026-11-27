"""문서 검색 도구 (패턴 2·4): retrieve_docs 와 contexts 항목 형식(ctx_entry).

에이전트 도구 전체 목록은 src/diagnosis/react.py 의 TOOLS 에 모은다(읽기·제안 도구만, D-8).
"""
from __future__ import annotations

from langchain_core.tools import tool

from src.knowledge.retriever import get_retriever


@tool(response_format="content_and_artifact")
def retrieve_docs(query_ko: str, query_en: str = "") -> tuple[str, list[dict]]:
    """Gemini Enterprise 공식 문서(SharePoint 커넥터, Entra ID, Workforce Identity Federation 등)를 검색한다.

    Args:
        query_ko: 한국어 검색어 (사용자 문의의 증상 요약)
        query_en: 영어 검색어 (문서가 영어이므로 핵심 용어를 영어로)
    """
    chunks = get_retriever().search([query_ko, query_en], k=5)
    lines, artifact = [], []
    for c in chunks:
        lines.append(f"[{c.chunk_id}] ({c.title} > {c.section})\n{c.text[:900]}")
        artifact.append(ctx_entry(c))
    return "\n\n".join(lines) or "검색 결과 없음", artifact


DOC_DATE = "2026-11-25"


def ctx_entry(c) -> dict:
    """[2차] contexts 항목. 본문 앞에 문서 ID·제목·출처·라이선스·수집일을 붙여, 답변의 출처 표기도 근거로 확인되게 한다."""
    head = f"[{c.chunk_id}] {c.title} - {c.section} (Gemini Enterprise 공식 문서, CC BY 4.0, 수집 기준일 {DOC_DATE})"
    return {"doc_id": c.chunk_id, "text": f"{head}\n{c.text}", "title": c.title, "section": c.section, "url": c.url}
