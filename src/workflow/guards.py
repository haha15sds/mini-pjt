"""그래프의 입구·출구 노드: 입력 재검사(남은 개인정보·인젝션), 출력 재마스킹."""
from __future__ import annotations

from src.guardrails import detect_injection, mask_pii, residual_pii
from src.workflow.answer import compose_answer
from src.workflow.state import State, trace_entry


def input_guard(state: State) -> dict:
    q = state["question"]
    residual = residual_pii(q)
    inj = detect_injection(q)
    blocked = bool(residual)
    return {"blocked": blocked, "injection": inj,
            "trace": [trace_entry("input_guard", {"length": len(q)}, {"residual_pii": residual, "injection_patterns": len(inj), "blocked": blocked})]}


def output_guard(state: State) -> dict:
    ans, kinds = mask_pii(compose_answer(state))
    return {"answer": ans, "trace": [trace_entry("output_guard", {"remasked": kinds}, ans[:300])]}
