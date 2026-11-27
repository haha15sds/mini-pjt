"""단일 진입점 handle_query 와 체크포인트 (D-7·D-12).

handle_query(question, thread_id=None, decision=None, scenario_id=None)
FastAPI·Streamlit·평가 실행기가 모두 이 함수만 부른다. 그래프 실행 전에 mask_pii 를 먼저 한다(D-6).
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from src import tenant
from src.guardrails import mask_pii
from src.utils.paths import ROOT
from src.workflow.answer import compose_answer
from src.workflow.graph import build_graph
from src.workflow.state import CHECK

MAX_LEN = 4000

DB_PATH = Path(os.getenv("CHECKPOINT_DB", ROOT / "checkpoints.sqlite"))
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
graph = build_graph(SqliteSaver(_conn))


def reset_checkpoints() -> None:
    """평가 시작 때 checkpoint DB 를 비운다 (D-12)."""
    global graph, _conn
    _conn.close()
    if DB_PATH.exists():
        DB_PATH.unlink()
    _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    graph = build_graph(SqliteSaver(_conn))


def _err(msg: str, thread_id: str | None = None) -> dict:
    return {"answer": f"요청 오류: {msg}", "contexts": [], "trace": [{"step": "validate", "input": "", "output": msg}],
            **({"thread_id": thread_id} if thread_id else {})}


def _response(st: dict, thread_id: str, waiting: bool) -> dict:
    ctx = [{"doc_id": c["doc_id"], "text": c["text"]} for c in st.get("contexts", [])]
    answer = st.get("answer") if not waiting else mask_pii(compose_answer(st, waiting=True))[0]
    res = {"answer": answer or CHECK, "contexts": ctx, "trace": st.get("trace", []), "thread_id": thread_id,
           "approval_required": waiting}
    if st.get("diagnosis"):
        res["diagnosis"] = {"causes": st["diagnosis"]["causes"], "steps": st["diagnosis"]["steps"]}
    if waiting and st.get("pending_action"):
        res["pending_action"] = st["pending_action"]
    return res


def handle_query(question: str = "", thread_id: str | None = None, decision: str | None = None,
                 scenario_id: str | None = None) -> dict:
    """FastAPI·Streamlit·평가 실행기의 공통 진입점. 항상 answer·contexts·trace 3필드를 돌려준다."""
    try:
        if decision is not None:
            if decision not in ("approve", "reject"):
                return _err("decision은 approve 또는 reject만 가능합니다.")
            if not thread_id:
                return _err("decision을 보낼 때는 thread_id가 필요합니다.")
            if not tenant.has_thread(thread_id):
                return _err("존재하지 않는 thread_id입니다.")
            cfg = {"configurable": {"thread_id": thread_id}}
            snap = graph.get_state(cfg)
            if not snap.next:
                st = dict(snap.values)
                res = _response(st, thread_id, waiting=False)
                res["answer"] = "이미 처리가 끝난 요청입니다. 조치는 다시 적용되지 않습니다.\n" + (res["answer"] or "")
                return res
            st = graph.invoke(Command(resume=decision), cfg)
            return _response(st, thread_id, waiting=False)

        if not question or not question.strip():
            return _err("질문이 비어 있습니다.")
        if len(question) > MAX_LEN:
            return _err(f"질문이 {MAX_LEN:,}자를 넘습니다.")
        masked, kinds = mask_pii(question)          # D-6: 그래프 실행 전 마스킹
        thread_id = thread_id or f"t-{uuid.uuid4().hex[:12]}"
        sid = scenario_id or os.getenv("DEFAULT_SCENARIO", "S00")
        if sid not in tenant.SCENARIOS:
            return _err(f"알 수 없는 scenario_id입니다: {sid}")
        tenant.ensure_thread(thread_id, sid)        # D-2: 장애 주입은 그래프 밖에서
        cfg = {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}
        st = graph.invoke({"question": masked, "scenario_id": sid, "detected_types": kinds,
                           "trace": [{"step": "mask_pii", "input": f"{len(question)}자", "output": f"가린 종류: {kinds or '없음'}"}]}, cfg)
        waiting = bool(graph.get_state(cfg).next)
        return _response(st, thread_id, waiting)
    except Exception as e:  # fail-closed: 오류 내용에 원문이 섞이지 않게 마스킹
        return _err(mask_pii(f"처리 중 오류가 발생했습니다 ({type(e).__name__}).")[0], thread_id)


if __name__ == "__main__":   # 실행: python -m src.workflow.entry
    q = "안녕하세요. 연구소 사이트 문서만 Gemini 검색에 안 나옵니다. 선택한 사이트에만 앱 권한을 주는 방식입니다."
    r = handle_query(q, scenario_id="S04")
    print(json.dumps({k: v for k, v in r.items() if k != "contexts"}, ensure_ascii=False, indent=1)[:3000])
    if r.get("approval_required"):
        r2 = handle_query(thread_id=r["thread_id"], decision="approve")
        print(r2["answer"])
        print(tenant.get_state(r["thread_id"])["sharepoint"]["sites"])
