"""Gemini Enterprise 설정 지원 에이전트 - Streamlit 화면 (D-13).

실행: streamlit run app.py
- 에이전트는 handle_query 만 부른다(D-7). 화면에는 마스킹된 텍스트만 보인다.
- '샘플 응답으로 보기'를 켜면 Bedrock 호출 없이 저장된 샘플(data/demo/sample_response.json)로 화면을 보여 준다.
- 화면 구성은 docs/prototype/index.html 프로토타입을 따른다:
  상단 바 / 좌측 진행 단계 / 가운데 ①입력 ②진단 ③승인 ④전후 비교 / 우측 근거 문서·trace·가드레일
"""
from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import tenant  # noqa: E402
from guardrails import detect_injection, mask_pii  # noqa: E402

st.set_page_config(page_title="GE 설정 지원 에이전트", page_icon="🛠️", layout="wide")

RISK = {"low": ("낮음", "var(--ok)"), "med": ("중간", "var(--warn)"), "high": ("높음", "var(--bad)")}
NODES = ["mask_pii", "input_guard", "analyze", "agent", "plan_runbook", "approval_gate", "output_guard"]
NODE_KO = {"mask_pii": "마스킹", "input_guard": "입력 검사", "analyze": "분석", "agent": "에이전트",
           "plan_runbook": "런북 계획", "approval_gate": "승인 게이트", "output_guard": "출력 검사"}

# ---------------- 디자인 (프로토타입과 같은 토큰) ----------------
st.markdown("""
<style>
:root{--brand:#2f5bea;--brand-soft:#e8eefe;--ok:#1a7f4b;--ok-soft:#e3f5ea;--warn:#b26a00;--warn-soft:#fff1d6;
--bad:#c62f3c;--bad-soft:#fde7e9;--tok:#fff1a8;--tok-ink:#5c4400;--line:#e3e8f0;--muted:#5d6779;--soft:#f5f7fb}
@media (prefers-color-scheme: dark){:root{--brand:#7d9bff;--brand-soft:#1f2b4a;--ok:#4cc38a;--ok-soft:#173326;--warn:#f0b450;
--warn-soft:#3a2d12;--bad:#ff7a85;--bad-soft:#3b1c22;--tok:#5a4a12;--tok-ink:#ffe9a3;--line:#283246;--muted:#9aa5b8;--soft:#121826}}
.block-container{padding-top:3rem;max-width:1500px}
.topbar{display:flex;align-items:center;gap:14px;padding:10px 4px 14px;border-bottom:1px solid var(--line);margin-bottom:14px}
.logo{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,#2f5bea,#7a5cff);display:grid;place-items:center;color:#fff;font-weight:800}
.ttl b{display:block;font-size:1.15rem}.ttl span{color:var(--muted);font-size:.85rem}
.chip{display:inline-block;padding:3px 10px;border-radius:999px;background:var(--brand-soft);color:var(--brand);font-size:.8rem;font-weight:700}
.num{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--brand);color:#fff;font-size:.8rem;font-weight:700;margin-right:6px}
.sec{font-size:1.02rem;font-weight:700;margin:2px 0 10px}
.stp{display:flex;gap:10px;align-items:flex-start;padding:9px 2px;color:var(--muted)}
.stp i{width:20px;height:20px;border-radius:50%;border:2px solid var(--line);flex:none;margin-top:3px}
.stp.on{color:inherit;font-weight:700}.stp.on i{border-color:var(--brand);background:var(--brand-soft)}
.stp.done i{background:var(--ok);border-color:var(--ok)}
.stp small{display:block;font-weight:400;font-size:.75rem;color:var(--muted)}
.prev{border:1px dashed var(--line);border-radius:10px;padding:12px;background:var(--soft);white-space:pre-wrap;min-height:205px;font-size:.92rem}
.tok{background:var(--tok);color:var(--tok-ink);border-radius:4px;padding:0 4px;font-weight:700}
.inj{background:var(--bad-soft);color:var(--bad);border-radius:4px;padding:0 3px;text-decoration:line-through}
.node{display:inline-block;padding:5px 11px;margin:2px 0;border-radius:8px;border:1px solid var(--line);font-size:.82rem;color:var(--muted)}
.node.on{background:var(--brand);border-color:var(--brand);color:#fff}.node.wait{background:var(--warn);border-color:var(--warn);color:#fff}
.arr{color:var(--muted);margin:0 3px}
.toolc{background:var(--brand-soft);color:var(--brand);padding:1px 7px;border-radius:5px;font-family:ui-monospace,Consolas,monospace;font-size:.8rem}
.ans{background:var(--soft);border-left:4px solid var(--brand);border-radius:8px;padding:12px 14px;white-space:pre-wrap;font-size:.95rem}
.cause{border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:10px}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.75rem;font-weight:800;color:#fff;background:var(--brand)}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:8px 0 3px}.bar b{display:block;height:100%;background:linear-gradient(90deg,#2f5bea,#7a5cff)}
.evi span{display:inline-block;font-size:.75rem;padding:1px 7px;margin:4px 4px 0 0;border-radius:6px;border:1px solid var(--line);font-family:ui-monospace,Consolas,monospace}
.tl{position:relative;padding-left:22px}.tl:before{content:"";position:absolute;left:8px;top:6px;bottom:6px;width:2px;background:var(--line)}
.ts{position:relative;margin:0 0 12px;font-size:.93rem}.ts:before{content:"";position:absolute;left:-19px;top:6px;width:12px;height:12px;border-radius:50%;background:inherit;border:3px solid var(--c)}
.risk{font-size:.7rem;font-weight:800;padding:1px 7px;border-radius:999px;color:#fff;background:var(--c)}
.muted{color:var(--muted);font-size:.82rem}
.apv{border:2px solid var(--warn);background:var(--warn-soft);border-radius:12px;padding:14px 16px}
.diff{width:100%;border-collapse:collapse;font-size:.9rem}.diff td,.diff th{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.diff th{color:var(--muted);font-size:.75rem}.old{color:var(--bad);text-decoration:line-through}.new{color:var(--ok);font-weight:700}
.doc{border:1px solid var(--line);border-radius:10px;padding:9px 10px;margin-bottom:8px;font-size:.82rem}
.doc b{font-family:ui-monospace,Consolas,monospace;color:var(--brand)}
.tr{font-size:.8rem;margin:0 0 5px;color:var(--muted)}.tr b{color:inherit}
.foot{color:var(--muted);font-size:.75rem;text-align:center;padding:16px 0}
</style>""", unsafe_allow_html=True)

# ---------------- 상태 ----------------
ss = st.session_state
for k, v in {"resp": None, "before": None, "after": None, "question": "", "scenario": "S01", "demo": False, "decided": None}.items():
    ss.setdefault(k, v)


@st.cache_resource(show_spinner="검색 인덱스 준비 중... (처음 한 번)")
def _warm() -> int:
    from retriever import warm_up
    return warm_up()


def call_agent(**kw) -> dict:
    _warm()   # [추가 구현] 실제 에이전트를 처음 부를 때 인덱스를 먼저 준비
    from agent import handle_query  # Bedrock 클라이언트는 실제 호출 때만 불러온다
    return handle_query(**kw)


def masked_html(text: str) -> tuple[str, list[str], bool]:
    masked, kinds = mask_pii(text or "")
    inj = bool(detect_injection(masked))
    h = html.escape(masked)
    h = re.sub(r"\[(EMAIL|PHONE|SECRET|NAME)\]", r'<span class="tok">[\1]</span>', h)
    if inj:
        h = re.sub(r"(※[^\n]*)", r'<span class="inj">\1</span>', h)
    return h, kinds, inj


def esc(s) -> str:
    return html.escape(str(s))


# ---------------- 사이드바: 시연 도구 ----------------
rows = list(csv.DictReader(open(ROOT / "evaluation" / "test_queries.csv", encoding="utf-8-sig")))
with st.sidebar:
    st.markdown("### 시연 도구")
    ss.demo = st.toggle("샘플 응답으로 보기 (Bedrock 호출 없음)", value=ss.demo)
    pick = st.selectbox("예시 문의 불러오기", ["(직접 입력)"] + [f"{r['id']} · {r['category']}" for r in rows])
    if st.button("불러오기", width="stretch") and pick != "(직접 입력)":
        r = rows[[f"{x['id']} · {x['category']}" for x in rows].index(pick)]
        ss.question, ss.resp, ss.after, ss.decided = r["input"], None, None, None
        m = re.search(r"scenario=(S\d\d)", r["note"])
        if m:
            ss.scenario = m.group(1)
        st.rerun()
    if st.button("처음부터", width="stretch"):
        ss.resp, ss.after, ss.decided = None, None, None
        st.rerun()
    st.caption("모든 테넌트·메일 데이터는 가상입니다.")

# ---------------- 상단 바 ----------------
top_l, top_r = st.columns([5, 2])
with top_l:
    st.markdown("<div class='topbar'><div class='logo'>GE</div><div class='ttl'><b>Gemini Enterprise 설정 지원 에이전트</b>"
                "<span>근거 있는 진단, 승인 후 조치</span></div><span class='chip'>가상 테넌트 · 가상상사</span></div>",
                unsafe_allow_html=True)
with top_r:
    scen = {k: f"{k} · {v['title']}" for k, v in tenant.SCENARIOS.items()}
    ss.scenario = st.selectbox("시나리오", list(scen), index=list(scen).index(ss.scenario), format_func=scen.get,
                               help="장애는 그래프 밖에서 이 시나리오로 주입됩니다 (D-2)")

tab_main, tab_eval = st.tabs(["🔎 진단", "📊 평가 대시보드"])

with tab_main:
    resp = ss.resp
    stage = 1 if not resp else (4 if ss.decided else (3 if resp.get("approval_required") else 4))
    c_left, c_mid, c_right = st.columns([1.15, 4.2, 1.75], gap="medium")

    # ---- 좌측: 진행 단계 ----
    with c_left:
        with st.container(border=True):
            for n, (t, s) in enumerate([("문의 입력", "개인정보 자동 가림"), ("진단", "문서 검색 · 테넌트 조회"),
                                        ("승인", "관리자가 결정"), ("결과", "바뀐 설정 확인")], 1):
                cls = "done" if n < stage else ("on" if n == stage else "")
                st.markdown(f"<div class='stp {cls}'><i></i><div>{t}<small>{s}</small></div></div>", unsafe_allow_html=True)

    # ---- 가운데 ----
    with c_mid:
        with st.container(border=True):
            st.markdown("<div class='sec'><span class='num'>1</span>문의 입력</div>", unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                ss.question = st.text_area("관리자 문의 (전달받은 메일·오류 메시지 붙여넣기)", value=ss.question, height=230)
            with b:
                h, kinds, inj = masked_html(ss.question)
                st.markdown("<div class='muted' style='margin-bottom:6px'>에이전트에 전달되는 내용 (마스킹 미리보기)</div>"
                            f"<div class='prev'>{h or '<span class=muted>입력을 기다리는 중</span>'}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='muted'>가린 종류: {', '.join(kinds) or '없음'}"
                            + (" · <b style='color:var(--bad)'>붙여넣은 내용 속 지시 탐지 → 따르지 않음</b>" if inj else "") + "</div>",
                            unsafe_allow_html=True)
            run = st.button("진단 요청", type="primary")

        if run:
            if ss.demo:
                sample = json.loads((ROOT / "data" / "demo" / "sample_response.json").read_text(encoding="utf-8"))
                ss.resp, ss.scenario, ss.question = sample["response"], sample["scenario_id"], sample["question"]
                ss.before = tenant.initial_state(ss.scenario)
            else:
                with st.spinner("문서 검색 · 테넌트 조회 · 런북 작성 중..."):
                    ss.resp = call_agent(question=ss.question, scenario_id=ss.scenario)
                tid = ss.resp.get("thread_id")
                ss.before = tenant.get_state(tid) if tid and tenant.has_thread(tid) else tenant.initial_state(ss.scenario)
            ss.after, ss.decided = None, None
            st.rerun()

        if resp:
            # ② 진단
            steps = [t["step"] for t in resp.get("trace", [])]
            visited = {s for s in steps if s in NODES} | ({"agent"} if any(s.startswith("tool:") for s in steps) else set())
            if ss.decided:
                visited |= {"approval_gate", "output_guard"}
            nodes = []
            for n in NODES:
                cls = "wait" if (n == "approval_gate" and resp.get("approval_required") and not ss.decided) else ("on" if n in visited else "")
                nodes.append(f"<span class='node {cls}'>{NODE_KO[n]}</span>")
            tools = [s.split(":", 1)[1] for s in steps if s.startswith("tool:")]
            diag = resp.get("diagnosis") or {}
            causes = [c for c in diag.get("causes", []) if c["fault_id"] != "none"]
            with st.container(border=True):
                st.markdown("<div class='sec'><span class='num'>2</span>진단</div>"
                            + "<span class='arr'>→</span>".join(nodes)
                            + (f"<div class='muted' style='margin:8px 0 12px'>에이전트가 고른 도구: {' '.join(f'<span class=toolc>{t}</span>' for t in tools)}</div>" if tools else "")
                            + f"<div class='ans'>{esc(resp.get('answer', ''))}</div>", unsafe_allow_html=True)
                p, q = st.columns(2)
                with p:
                    st.markdown("<div class='muted' style='margin:12px 0 6px'>원인 후보</div>", unsafe_allow_html=True)
                    if not causes:
                        st.info("근거 있는 원인 후보가 없습니다 (확인 필요).")
                    for c in causes:
                        f = tenant.FAULTS.get(c["fault_id"], {})
                        st.markdown(f"<div class='cause'><span class='badge'>{c['fault_id']}</span> <b>{esc(f.get('name', ''))}</b>"
                                    f"<div class='bar'><b style='width:{c['confidence'] * 100:.0f}%'></b></div>"
                                    f"<div class='muted'>확신도 {c['confidence']:.0%} · {esc(c.get('reason', ''))}</div>"
                                    f"<div class='evi'>{''.join(f'<span>{esc(e)}</span>' for e in c['evidence_doc_ids'])}</div></div>",
                                    unsafe_allow_html=True)
                with q:
                    st.markdown("<div class='muted' style='margin:12px 0 6px'>조치 런북</div>", unsafe_allow_html=True)
                    tl = "".join(f"<div class='ts' style='--c:{RISK[s['risk']][1]}'><b>{i}.</b> {esc(s['action'])}<br>"
                                 f"<span class='risk' style='--c:{RISK[s['risk']][1]}'>위험 {RISK[s['risk']][0]}</span> "
                                 f"<span class='muted'>출처 <code>{esc(s['source'])}</code></span></div>"
                                 for i, s in enumerate(diag.get("steps", []), 1))
                    st.markdown(f"<div class='tl'>{tl}</div>", unsafe_allow_html=True)

            # ③ 승인
            pa = resp.get("pending_action")
            if resp.get("approval_required") and pa and not ss.decided:
                st.markdown(f"<div class='apv'><div class='sec'><span class='num'>3</span>승인이 필요한 조치</div>"
                            f"<span class='risk' style='--c:{RISK[pa['risk']][1]}'>위험 {RISK[pa['risk']][0]}</span> "
                            f"<code>{esc(pa['fix_id'])}</code> — {esc(pa['action'])}"
                            "<div class='muted' style='margin-top:6px'>승인 전에는 테넌트가 바뀌지 않습니다. 승인하면 승인 게이트 안에서만 조치가 실행되고, "
                            "같은 조치는 한 번만 적용됩니다.</div></div>", unsafe_allow_html=True)
                b1, b2, _ = st.columns([1.4, 1.4, 2])
                dec = "approve" if b1.button("✅ 승인", width="stretch", help="approve") else (
                      "reject" if b2.button("⛔ 거절", width="stretch", help="reject") else None)
                if dec:
                    if ss.demo:
                        tid = "t-demo"
                        tenant._TENANTS.pop(tid, None)
                        tenant._APPLIED.pop(tid, None)
                        tenant.ensure_thread(tid, ss.scenario)
                        if dec == "approve":
                            tenant.apply_fix(tid, pa["fix_id"])
                        ss.after = tenant.get_state(tid)
                        ss.resp = {**resp, "trace": resp.get("trace", []) + [{"step": "approval_gate", "input": dec, "output": "샘플"}]}
                    else:
                        with st.spinner("결정 반영 중..."):
                            ss.resp = call_agent(thread_id=resp["thread_id"], decision=dec)
                        ss.after = tenant.get_state(resp["thread_id"])
                    ss.decided = dec
                    st.toast("조치를 적용했습니다 (가상 테넌트)" if dec == "approve" else "거절했습니다 · 상태 변경 없음")
                    st.rerun()

            # ④ 전/후
            if ss.decided:
                with st.container(border=True):
                    st.markdown("<div class='sec'><span class='num'>4</span>가상 테넌트 상태 전/후</div>", unsafe_allow_html=True)
                    changes = tenant.diff(ss.before or {}, ss.after or {})
                    if changes:
                        rows_html = "".join(f"<tr><td><code>{esc(c['path'])}</code></td><td class='old'>{esc(json.dumps(c['before'], ensure_ascii=False))}</td>"
                                            f"<td class='new'>{esc(json.dumps(c['after'], ensure_ascii=False))}</td></tr>" for c in changes)
                        st.markdown(f"<table class='diff'><tr><th>설정</th><th>전</th><th>후</th></tr>{rows_html}</table>", unsafe_allow_html=True)
                    else:
                        st.info("관리자가 거절해 조치를 적용하지 않았습니다. 테넌트 상태는 그대로입니다.")
                    with st.expander("현재 테넌트 상태 전체"):
                        st.json(ss.after or {})

    # ---- 우측 ----
    with c_right:
        with st.container(border=True):
            st.markdown("**근거 문서**")
            ctx = (resp or {}).get("contexts", [])
            if not ctx:
                st.markdown("<span class='muted'>진단 후 표시됩니다.</span>", unsafe_allow_html=True)
            for c in ctx:
                first = c["text"].split("\n", 1)
                title = re.sub(r"^\[[^\]]+\]\s*", "", first[0])[:70]
                st.markdown(f"<div class='doc'><b>{esc(c['doc_id'])}</b><br>{esc(title)}</div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("**실행 기록 (trace)**")
            tr = (resp or {}).get("trace", [])
            st.markdown("".join(f"<div class='tr'>{i}. <b>{esc(t['step'])}</b> {esc(str(t['output'])[:60])}</div>" for i, t in enumerate(tr, 1))
                        or "<span class='muted'>대기 중</span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("**가드레일**")
            st.markdown("<div class='muted'>🔒 개인정보·시크릿 마스킹<br>🛡️ 붙여넣은 내용 속 지시 무시<br>✋ 승인 없는 변경 금지<br>📎 근거 없으면 \"확인 필요\"</div>",
                        unsafe_allow_html=True)

    st.markdown("<div class='foot'>테넌트·메일 데이터는 모두 가상입니다 · 근거 문서: Gemini Enterprise 공식 문서(CC BY 4.0, 수집 2026-11-25)"
                + (" · 샘플 응답 모드" if ss.demo else "") + "</div>", unsafe_allow_html=True)

# ================= 평가 대시보드 =================
with tab_eval:
    st.subheader("인-아웃 세트 평가 (18건)")
    ev = ROOT / "evaluation"
    rounds = {}
    for name, path in [("1차", ev / "round1_results.json"), ("2차", ev / "round2_results.json"), ("3차", ev / "round3_results.json"), ("4차", ev / "round4_results.json")]:
        if path.exists():
            rounds[name] = json.loads(path.read_text(encoding="utf-8"))
    if not rounds:
        st.info("평가 결과가 없습니다. `python evaluation/run_eval.py --round 1` 을 먼저 실행하세요.")
    else:
        cols = st.columns(len(rounds) + 1)
        for col, (name, res) in zip(cols, rounds.items()):
            col.metric(f"{name} 통과", f"{sum(r['passed'] for r in res)} / {len(res)}")
        cols[-1].metric("목표 (2차 이후)", "15 / 18")
        cat = []
        for name, res in rounds.items():
            for c in ["positive", "negative", "edge", "guardrail"]:
                rs = [r for r in res if r["category"] == c]
                cat.append({"라운드": name, "범주": c, "통과율": sum(r["passed"] for r in rs) / max(len(rs), 1)})
        st.markdown("**범주별 통과율**")
        st.bar_chart(pd.DataFrame(cat), x="범주", y="통과율", color="라운드", stack=False)
        rag = []
        resc = ev / "round1_results_rescored.json"
        src = {"1차": json.loads(resc.read_text(encoding="utf-8"))["results"] if resc.exists() else rounds.get("1차", [])}
        for nm in ("2차", "3차", "4차"):
            if nm in rounds:
                src[nm] = rounds[nm]
        for name, res in src.items():
            for k in ["faithfulness", "answer_relevancy", "llm_context_precision_with_reference", "context_recall"]:
                vals = [r["ragas"][k] for r in res if r.get("ragas") and r["ragas"].get(k) is not None]
                if vals:
                    rag.append({"라운드": name, "지표": k, "평균": sum(vals) / len(vals)})
        if rag:
            st.markdown("**RAGAS 4지표** (positive·edge, 채점 모델 Haiku 4.5 기준)")
            st.bar_chart(pd.DataFrame(rag), x="지표", y="평균", color="라운드", stack=False)
        last = list(rounds)[-1]
        st.markdown(f"**케이스별 결과 ({last})**")
        st.dataframe(pd.DataFrame([{"id": r["id"], "범주": r["category"], "준블라인드": "AI 작성" if r["semi_blind"] else "",
                                    "정답": r["expected_fault"], "1순위": r["top_fault"], "통과": "✅" if r["passed"] else "❌",
                                    "도구 일치": "✅" if r["tool_match"] else "❌", "초": r["seconds"]} for r in rounds[last]]),
                     width="stretch", hide_index=True)
