"""진단 구조화 노드 (Plan): 원인 후보·조치 런북을 만들고, 코드 점검으로 검증하고, 근거를 다시 찾는다."""
from __future__ import annotations

import re

from src import tenant
from src.diagnosis.prompts import PLAN_PROMPT
from src.diagnosis.schemas import Cause, Diagnosis, Step
from src.knowledge.retriever import get_retriever
from src.knowledge.tools import ctx_entry
from src.utils.llm import llm_main, llm_main_g
from src.utils.text import text_of
from src.workflow.state import CHECK, State, trace_entry

plan_chain = PLAN_PROMPT | llm_main.with_structured_output(Diagnosis).with_fallbacks([llm_main_g.with_structured_output(Diagnosis)])


def plan_runbook(state: State, config) -> dict:
    intent = state.get("analysis", {}).get("intent")
    if state.get("blocked"):
        return {"diagnosis": None, "pending_action": None, "trace": [trace_entry("plan_runbook", "blocked", "입력 차단")]}
    if intent == "secret_request":
        return {"diagnosis": None, "pending_action": None, "trace": [trace_entry("plan_runbook", "secret_request", "거절")]}
    if state.get("timed_out"):
        return {"diagnosis": None, "pending_action": None, "trace": [trace_entry("plan_runbook", "timeout", CHECK)]}
    ctx = state.get("contexts", [])
    notes = "\n".join(text_of(m) for m in state.get("messages", []))[-4000:]
    d = plan_chain.invoke({
        "faults": "\n".join(f"{k}: {v['name']} (대표 증상: {v['symptom']})" for k, v in tenant.FAULTS.items()),
        "fixes": "\n".join(f"{k} ({v['fault_id']}, {v['risk']}): {v['action']}" for k, v in tenant.FIXES.items()),
        "question": state["question"],
        "docs": "\n\n".join(f"[{c['doc_id']}] {c['section']}\n{c['text'][:4000 if c['doc_id'] == 'tenant-state' else 700]}" for c in ctx) or "(없음)",
        "notes": notes, "proposed": state.get("proposed") or "없음",
    })
    # [불일치 대응] 테넌트를 조회했다면, 원인 후보를 코드 점검 결과로 검증한다.
    #  - 테넌트에 근거가 없는 장애(문의 글만 보고 낸 원인)는 뺀다
    #  - 점검에서 확인된 실제 문제가 빠졌으면 보충한다
    #  - 증상과 맞지 않으면(모델 판단 또는 원인이 빠진 경우) 확신도를 0.5 이하로 낮추고 답변에 불일치를 밝힌다
    #  불일치 점검(M 세트) 1회차에서 좋음 0/8(끼워 맞춤 3·지어냄 2·실제 문제 누락 3)이라 추가했다.
    mismatch = not d.symptom_matches
    if any(c["doc_id"] == "tenant-state" for c in ctx):
        tid = (config or {}).get("configurable", {}).get("thread_id")
        sup = tenant.supported_faults(tenant.compute_checks(tenant.get_state(tid))) if tid else set()
        kept = [c for c in d.causes if c.fault_id == "none" or c.fault_id in sup]
        dropped = len(kept) != len(d.causes)
        real_kept = {c.fault_id for c in kept if c.fault_id != "none"}
        missing = sup - real_kept
        kept = [c for c in kept if c.fault_id != "none" or not missing]
        for fid in sorted(missing):
            kept.append(Cause(fault_id=fid, reason="테넌트 코드 점검(findings)에서 확인된 문제", confidence=0.5, evidence_doc_ids=["tenant-state"]))
        if dropped or (missing and not real_kept):
            mismatch = True
        d.causes = kept
        if mismatch:
            for c in d.causes:
                c.confidence = min(c.confidence, 0.5)
            # 요약에서 증상과 점검 결과를 잇는 연결 문장(근거 없는 추론)을 빼고 '테넌트 상태:'·'문서' 문장만 남긴다
            sents = [x.strip() for x in re.split(r"(?<=[.다])\s+", d.summary_ko) if x.strip()]
            keep = [x for x in sents if x.startswith(("테넌트 상태", "문서"))]
            if keep:
                d.summary_ko = " ".join(keep)
            # 조치 단계는 점검에서 확인된 문제의 조치 목록 항목과 '증상 원인 추가 확인'으로 바꾼다(증상 쪽 장애 조치가 섞이지 않게)
            real_ids = [c.fault_id for c in d.causes if c.fault_id != "none"]
            fx = [f for f in tenant.FIXES.values() if f["fault_id"] in real_ids]
            d.steps = [Step(action=f["action"], risk=f["risk"], source=f"fix:{f['fix_id']}") for f in fx] + [
                Step(action="문의하신 증상의 원인은 테넌트 점검에서 근거를 찾지 못했으므로, 증상이 나타나는 사용자·시점·오류 메시지를 추가로 확인한다",
                     risk="low", source="tenant-state")]
    # R5: 근거 doc_id 가 contexts 에 없는 원인은 버린다 (AC-5)
    # [2차] 버리기 전에, 공식 문서 근거가 없는 원인은 그 장애의 이름·근거 요약으로 한 번 더 검색해 본다(원인별 근거 재검색).
    #       1차 E1(장애 2개)에서 두 원인이 모두 근거 부족으로 지워졌다.
    ctx = list(ctx)
    ids = {c["doc_id"] for c in ctx}
    causes = []
    for c in d.causes:
        c.evidence_doc_ids = [x for x in c.evidence_doc_ids if x in ids]
        if c.fault_id != "none":
            # [개선 9차 후] 원인 중심 재검색을 모든 원인에 한다. 처음 검색어는 증상 문장에서 나와 일반 문제 해결 문서가
            # 앞에 깔리고, 원인 근거 문서는 빠지거나 맨 뒤에 붙었다(context_precision P5 0.17·E1 0.23·P6 0.25·E4 0.33).
            # 검색어는 장애 이름과 모델이 쓴 원인 설명이다. 평가 reference에 쓰는 evidence_note는 검색어에서 뺐다(평가 누설 방지).
            f = tenant.FAULTS[c.fault_id]
            # 장애 F1~F6은 모두 SharePoint 커넥터 장애라 다른 커넥터 문서(Confluence)는 근거에서 뺀다.
            # 반복 실행에서 E2(F2, 쓰기 scope)의 재검색 1위가 Confluence 'minimum application scopes'였다.
            hits = [ch for ch in get_retriever().search([f["name"], c.reason], k=4) if not ch.doc_id.startswith("ge-confluence")]
            for ch in hits[:2]:
                if ch.chunk_id not in ids:
                    ctx.append(ctx_entry(ch))
                    ids.add(ch.chunk_id)
                if ch.chunk_id not in c.evidence_doc_ids:
                    c.evidence_doc_ids.insert(0, ch.chunk_id)
        if c.fault_id == "none" or c.evidence_doc_ids:
            causes.append(c)
    d.causes = causes
    real = [c for c in causes if c.fault_id != "none"]
    pending = None
    fix_id = d.fix_id or (state.get("proposed") or [None])[0]
    # [불일치 대응] 제안 조치는 1순위 원인과 같은 장애의 조치여야 한다(증상 쪽 장애의 조치가 승인 카드에 뜨지 않게)
    if real and (fix_id not in tenant.FIXES or tenant.FIXES[fix_id]["fault_id"] != real[0].fault_id):
        fix_id = next((k for k, f in tenant.FIXES.items() if f["fault_id"] == real[0].fault_id), None)
    if real and fix_id in tenant.FIXES and intent == "sharepoint_issue":
        pending = {"fix_id": fix_id, "risk": tenant.FIXES[fix_id]["risk"], "action": tenant.FIXES[fix_id]["action"]}
        # [3차] propose_fix 호출 없이 계획 단계에서 조치를 고른 경우에도 조치 설명(승인 필요 포함)을 근거로 남긴다.
        if f"fix:{fix_id}" not in {c["doc_id"] for c in ctx}:
            f = tenant.FIXES[fix_id]
            ctx.append({"doc_id": f"fix:{fix_id}", "text": f"[fix:{fix_id}] 조치 목록(fix catalog) 항목 - {f['action']} "
                        f"(대상 장애 {f['fault_id']}, 위험도 {f['risk']}). 이 조치는 관리자가 승인(approve)한 뒤에만 적용된다.",
                        "title": "fix catalog", "section": fix_id, "url": ""})
    # [개선 9차 후] contexts 순서: 원인 근거 문서(원인 순) → 테넌트 상태·조치 목록 → 나머지 검색 결과.
    #  관리자가 읽는 근거 목록도 원인 근거가 앞에 오고, 순서를 보는 context_precision도 이 순서로 매긴다.
    first = [x for c in d.causes for x in c.evidence_doc_ids if x != "tenant-state" and not x.startswith("fix:")]
    rank = {x: i for i, x in enumerate(dict.fromkeys(first))}

    def _order(c):
        if c["doc_id"] in rank:
            return (0, rank[c["doc_id"]])
        return (1, 0) if c["doc_id"] == "tenant-state" or c["doc_id"].startswith("fix:") else (2, 0)
    ctx = sorted(ctx, key=_order)
    dd = d.model_dump()
    # 원인 후보가 하나도 없으면(범위 밖·정상 테넌트) 불일치 안내는 붙이지 않는다 — 7차에서 N4(가격 문의)에 잘못 붙었다
    dd["mismatch"] = mismatch and any(c.fault_id != "none" for c in d.causes)
    return {"diagnosis": dd, "pending_action": pending, "contexts": ctx,
            "trace": [trace_entry("plan_runbook", {"contexts": len(ctx)}, dd)]}
