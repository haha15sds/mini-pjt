"""문의 분석 노드 (LCEL 구조화 출력): 의도·증상·검색어를 뽑는다."""
from __future__ import annotations

from src.diagnosis.prompts import ANALYZE_PROMPT
from src.diagnosis.schemas import Analysis
from src.guardrails import SECRET_REQUEST
from src.utils.llm import llm_fast, llm_fast_g
from src.workflow.state import State, trace_entry

analyze_chain = ANALYZE_PROMPT | llm_fast.with_structured_output(Analysis).with_fallbacks([llm_fast_g.with_structured_output(Analysis)])   # LCEL


def analyze(state: State) -> dict:
    if state.get("blocked"):
        return {}
    a = analyze_chain.invoke({"question": state["question"]})
    if SECRET_REQUEST.search(state["question"]):
        a.intent = "secret_request"
    return {"analysis": a.model_dump(), "trace": [trace_entry("analyze", state["question"][:300], a.model_dump())]}
