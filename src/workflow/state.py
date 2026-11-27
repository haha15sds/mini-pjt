"""그래프 상태(State)와 노드 공통 도구: trace 항목 만들기, '확인 필요' 문구."""
from __future__ import annotations

import json
import operator
from typing import Annotated, Optional, TypedDict

from src.guardrails import mask_pii

CHECK = "확인 필요"


class State(TypedDict, total=False):
    question: str
    scenario_id: str
    detected_types: list[str]
    injection: list[str]
    blocked: bool
    analysis: dict
    messages: list
    contexts: list[dict]
    proposed: list[str]
    diagnosis: dict
    pending_action: Optional[dict]
    decision: Optional[str]
    apply_result: Optional[str]
    timed_out: bool
    answer: str
    trace: Annotated[list[dict], operator.add]


def trace_entry(step: str, inp, out) -> dict:
    """trace 한 줄. 입력·출력은 1,500자로 자르고 다시 마스킹한다(원문 유출 방지)."""
    s = lambda x: x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)
    return {"step": step, "input": mask_pii(s(inp)[:1500])[0], "output": mask_pii(s(out)[:1500])[0]}
