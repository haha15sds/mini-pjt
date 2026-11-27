"""ReAct 에이전트 노드 (패턴 2·4): 도구를 스스로 골라 근거(contexts)를 모은다. 도구는 읽기·제안뿐이다(D-8)."""
from __future__ import annotations

import concurrent.futures as cf

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src import tenant
from src.diagnosis.prompts import AGENT_SYSTEM
from src.knowledge.tools import retrieve_docs
from src.tenant.tools import check_tenant_state, propose_fix
from src.utils.llm import llm_main, llm_main_g
from src.utils.text import text_of
from src.workflow.state import State, trace_entry

MAX_STEPS = 8          # ReAct 최대 단계 (D-11)
TIMEOUT_S = 60         # 요청당 시간 상한 (D-11)
TOOLS = [retrieve_docs, check_tenant_state, propose_fix]
TOOL_MAP = {t.name: t for t in TOOLS}


def _run_react(state: State, config) -> dict:
    a = state.get("analysis", {})
    msgs = [SystemMessage(AGENT_SYSTEM),
            HumanMessage(f"문의:\n{state['question']}\n\n분석: intent={a.get('intent')}, 증상={a.get('symptoms')}\n"
                         f"검색어 제안: ko='{a.get('ko_query')}', en='{a.get('en_query')}'")]
    llm_tools = llm_main.bind_tools(TOOLS).with_fallbacks([llm_main_g.bind_tools(TOOLS)])
    contexts, proposed, trace = [], [], []
    for step in range(MAX_STEPS):
        ai = llm_tools.invoke(msgs, config=config)   # [수정] 별도 스레드에서도 그래프 트레이스(LangSmith) 아래에 기록되도록 노드 config 를 넘긴다
        msgs.append(ai)
        if not ai.tool_calls:
            break
        for tc in ai.tool_calls:
            tool = TOOL_MAP.get(tc["name"])
            if tool is None:
                msgs.append(ToolMessage(f"알 수 없는 도구: {tc['name']}", tool_call_id=tc["id"], status="error"))
                continue
            tm = tool.invoke({**tc, "type": "tool_call"}, config=config)
            msgs.append(tm)
            if tc["name"] == "retrieve_docs" and tm.artifact:
                contexts += [c for c in tm.artifact if c["doc_id"] not in {x["doc_id"] for x in contexts}]
            # [2차] 테넌트 조회 결과와 제안 조치도 근거(contexts)로 남긴다. 1차에서는 답이 테넌트 상태를 근거로
            # 말하는데 contexts에 없어 faithfulness가 낮게 나왔다.
            if tc["name"] == "check_tenant_state" and "tenant-state" not in {x["doc_id"] for x in contexts}:
                contexts.append({"doc_id": "tenant-state", "text": "[tenant-state] 가상 테넌트 현재 상태(check_tenant_state 결과)\n" + text_of(tm), "title": "가상 테넌트 상태",
                                 "section": "check_tenant_state", "url": ""})
            if tc["name"] == "propose_fix" and not text_of(tm).startswith("오류"):
                fid = tc["args"].get("fix_id")
                proposed.append(fid)
                if f"fix:{fid}" not in {x["doc_id"] for x in contexts}:
                    f = tenant.FIXES[fid]
                    contexts.append({"doc_id": f"fix:{fid}", "text": f"[fix:{fid}] 조치 목록(fix catalog) 항목 - {f['action']} "
                                     f"(대상 장애 {f['fault_id']}, 위험도 {f['risk']}). 이 조치는 관리자가 승인(approve)한 뒤에만 적용된다.",
                                     "title": "fix catalog", "section": fid, "url": ""})
            trace.append(trace_entry(f"tool:{tc['name']}", tc["args"], text_of(tm)[:600]))
    return {"messages": msgs, "contexts": contexts, "proposed": proposed, "trace": trace}


def agent(state: State, config) -> dict:
    if state.get("blocked") or state.get("analysis", {}).get("intent") == "secret_request":
        return {"contexts": [], "proposed": [], "trace": [trace_entry("agent", "skip", "차단 또는 비밀값 요청으로 도구 실행 안 함")]}
    # [리뷰 수정] with 블록은 빠져나올 때 작업이 끝날 때까지 기다려 60초 상한이 걸리지 않았다.
    # 상한을 넘으면 기다리지 않고 바로 돌려준다(남은 스레드는 읽기·제안 도구만 쓰므로 상태를 바꾸지 않는다).
    ex = cf.ThreadPoolExecutor(1)
    fut = ex.submit(_run_react, state, config)
    try:
        out = fut.result(timeout=TIMEOUT_S)
    except cf.TimeoutError:
        return {"timed_out": True, "contexts": [], "proposed": [], "trace": [trace_entry("agent", "react", f"{TIMEOUT_S}초 초과")]}
    finally:
        ex.shutdown(wait=False)
    out["messages"] = [m.model_dump() if hasattr(m, "model_dump") else m for m in out["messages"]][-4:]
    return out
