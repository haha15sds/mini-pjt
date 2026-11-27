"""승인 게이트 노드 (패턴 7, HITL): 그래프에서 유일하게 interrupt 하는 곳. 승인(approve)일 때만 조치를 적용한다(D-3)."""
from __future__ import annotations

from langgraph.types import interrupt

from src import tenant
from src.workflow.state import State, trace_entry

REJECT_MSG = "관리자가 거절하여 조치를 적용하지 않았습니다. 테넌트 상태는 그대로입니다."


def approval_gate(state: State, config) -> dict:
    pa = state.get("pending_action")
    if not pa:
        return {"trace": [trace_entry("approval_gate", "no pending action", "통과")]}
    decision = interrupt({"type": "approval", "pending_action": pa})   # HITL (패턴 7)
    tid = config["configurable"]["thread_id"]
    if decision == "approve":
        ok, msg = tenant.apply_fix(tid, pa["fix_id"])
    else:
        msg = REJECT_MSG
    return {"decision": decision, "apply_result": msg,
            "trace": [trace_entry("approval_gate", {"decision": decision, "fix_id": pa["fix_id"]}, msg)]}
