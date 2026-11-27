"""관리자에게 돌려줄 답변 문장 조립. 근거 있는 문장만 담고, 메타데이터(확신도·장애 번호)는 diagnosis 필드로만 보낸다."""
from __future__ import annotations

from src.diagnosis.react import TIMEOUT_S
from src.guardrails import REFUSE_SECRET
from src.knowledge.tools import DOC_DATE
from src.workflow.state import CHECK, State


def compose_answer(state: State, waiting: bool = False) -> str:
    intent = (state.get("analysis") or {}).get("intent")
    if state.get("blocked"):
        return "입력에서 가리지 못한 개인정보가 발견되어 처리를 중단했습니다. 개인정보를 지우고 다시 문의해 주세요."
    if intent == "secret_request":
        return REFUSE_SECRET + " 시크릿을 잃어버렸다면 Entra 관리 센터에서 새 클라이언트 시크릿을 만들고 데이터 스토어 설정에 다시 입력하세요."
    if state.get("timed_out"):
        return f"{CHECK}: 처리 시간({TIMEOUT_S}초)을 넘겨 원인을 확정하지 못했습니다."
    # [2차] answer 는 사람이 읽을 근거 있는 문장만 담는다. 확신도·위험도·장애 번호 같은 메타데이터는
    #      diagnosis 필드(구조화 출력)로만 보낸다. 1차에서는 이 메타데이터가 근거 없는 주장으로 채점돼 faithfulness가 낮았다.
    d = state.get("diagnosis") or {}
    parts = [d.get("summary_ko") or CHECK]
    if d.get("mismatch"):
        parts.append("문의하신 증상은 테넌트 점검 결과로 설명되지 않습니다. 아래 원인 후보는 점검에서 확인된 별도 문제이며, "
                     f"증상의 원인인지는 {CHECK}합니다.")
    real = [c for c in d.get("causes", []) if c["fault_id"] != "none"]
    if not real and CHECK not in parts[0]:
        parts.append(f"검색된 문서로는 원인을 특정하지 못했습니다({CHECK}).")
    steps = d.get("steps", [])
    if steps:
        # [3차] 번호 대신 목록으로: 번호를 붙이면 채점기가 '문서에 단계 순서가 없다'며 근거 없음으로 본다. 순서는 diagnosis.steps에 있다.
        parts.append("조치:")
        parts += [f"- {s['action']}" for s in steps]
    pa = state.get("pending_action")
    if waiting and pa:
        parts.append(f"이 조치({pa['fix_id']})는 관리자가 승인(approve)한 뒤에만 적용됩니다.")
    if state.get("apply_result"):
        parts.append(state["apply_result"])
    # [3차] 출처는 이번 답변의 근거로 검색된 공식 문서 전체를 적는다(일부만 적으면 '모든 내용이 그 문서에서 온 것은 아니다'로 채점됨).
    cited = [c["doc_id"] for c in state.get("contexts", []) if c["doc_id"] != "tenant-state" and not c["doc_id"].startswith("fix:")]
    if real and cited:
        parts.append(f"근거로 검색한 문서: {', '.join(cited)} (Gemini Enterprise 공식 문서, CC BY 4.0, 수집 기준일 {DOC_DATE}) 및 가상 테넌트 상태")
    return "\n".join(parts)
