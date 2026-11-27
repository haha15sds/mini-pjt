"""Gemini Enterprise 설정 지원 에이전트 - Streamlit 화면 (D-13).

실행: streamlit run src/ui/app.py   (저장소 루트에서)
- 에이전트는 handle_query 만 부른다(D-7). 화면에는 마스킹된 텍스트만 보인다.
- '샘플 응답으로 보기'를 켜면 Bedrock 호출 없이 저장된 샘플(data/demo/sample_response.json)로 화면을 보여 준다.
- 화면 구성은 docs/prototype/index.html 프로토타입을 따른다:
  상단 바 / 좌측 진행 단계 / 가운데 ①입력 ②진단 ③승인 ④전후 비교 / 우측 근거 문서·trace·가드레일
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]   # 저장소 루트
sys.path.insert(0, str(ROOT))                # streamlit 은 스크립트 폴더만 경로에 넣으므로 루트를 더해 src 패키지를 찾게 한다

from src import tenant  # noqa: E402
from src.guardrails import detect_injection, mask_pii  # noqa: E402

st.set_page_config(page_title="GE 설정 지원 에이전트", page_icon=":material/build:", layout="wide")

RISK = {"low": ("낮음", "var(--ok-solid)"), "med": ("중간", "var(--warn-solid)"), "high": ("높음", "var(--bad-solid)")}
NODES = ["mask_pii", "input_guard", "analyze", "agent", "plan_runbook", "approval_gate", "output_guard"]
NODE_KO = {"mask_pii": "마스킹", "input_guard": "입력 검사", "analyze": "분석", "agent": "에이전트",
           "plan_runbook": "런북 계획", "approval_gate": "승인 게이트", "output_guard": "출력 검사"}

# ---------------- 디자인 (프로토타입과 같은 토큰) ----------------
st.markdown("""
<style>
/* Hallmark · redesign: polish · shape: app screen · genre: modern-minimal · posture: restrained · 프로토타입(docs/prototype/index.html)과 같은 기준 */
:root{--brand:#2f5bea;--brand-soft:#e8eefe;--ok:#1a7f4b;--ok-soft:#e3f5ea;--warn:#9a5a00;--warn-soft:#fff1d6;
--bad:#c62f3c;--bad-soft:#fde7e9;--tok:#fff1a8;--tok-ink:#5c4400;--line:#dfe5ee;--muted:#5a6476;--soft:#f5f7fb;
--on-solid:#ffffff;--brand-solid:#2f5bea;--ok-solid:#1a7f4b;--warn-solid:#9a5a00;--bad-solid:#b42834;--mono:ui-monospace,Consolas,monospace}
@media (prefers-color-scheme: dark){:root{--brand:#8aa6ff;--brand-soft:#1f2b4a;--ok:#5fd09a;--ok-soft:#173326;--warn:#f0b450;
--warn-soft:#3a2d12;--bad:#ff8a94;--bad-soft:#3b1c22;--tok:#5a4a12;--tok-ink:#ffe9a3;--line:#2b3549;--muted:#a3adbf;--soft:#121826;
--brand-solid:#3355d6;--ok-solid:#18704a;--warn-solid:#8a5200;--bad-solid:#b02a36}}
html,body{overflow-x:clip}
.block-container{padding-top:3rem;max-width:1500px}
.topbar{display:flex;align-items:center;gap:16px;padding:8px 4px 16px;border-bottom:1px solid var(--line);margin-bottom:16px}
.logo{width:40px;height:40px;border-radius:8px;background:var(--brand-solid);display:grid;place-items:center;color:var(--on-solid);font-weight:800}
.wordmark{margin:0;font-size:1.15rem;font-weight:700;line-height:1.3}.tagline{margin:0;font-size:.85rem}
.chip{display:inline-block;padding:4px 12px;border-radius:999px;background:var(--brand-soft);font-size:.8rem;font-weight:700}
.num{display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--brand-solid);color:var(--on-solid);font-size:.8rem;font-weight:700;margin-right:8px}
.sec{font-size:1.02rem;font-weight:700;margin:0 0 12px;text-wrap:balance}
.stp{display:flex;gap:12px;align-items:flex-start;padding:8px 0;color:var(--muted)}
.stp .no{width:24px;height:24px;border-radius:50%;border:2px solid var(--line);flex:none;display:grid;place-items:center;font-size:.75rem;font-weight:700}
.stp.on{color:inherit;font-weight:700}.stp.on .no{border-color:var(--brand);color:var(--brand)}
.stp.done .no{background:var(--ok-solid);border-color:var(--ok-solid);color:var(--on-solid)}
.stp small{display:block;font-weight:400;font-size:.75rem;color:var(--muted)}
.prev{border:1px dashed var(--line);border-radius:8px;padding:12px;background:var(--soft);white-space:pre-wrap;min-height:204px;font-size:.92rem}
.tok{background:var(--tok);color:var(--tok-ink);border-radius:4px;padding:0 4px;font-weight:700}
.inj{background:var(--bad-soft);color:var(--bad);border-radius:4px;padding:0 4px;text-decoration:line-through}
.node{display:inline-block;padding:4px 12px;margin:4px 0;border-radius:8px;border:1px solid var(--line);font-size:.82rem;color:var(--muted)}
.node.on{background:var(--brand-solid);border-color:var(--brand-solid);color:var(--on-solid)}.node.wait{background:var(--warn-solid);border-color:var(--warn-solid);color:var(--on-solid)}
.arr{color:var(--muted);margin:0 4px}
.toolc{background:var(--brand-soft);padding:2px 8px;border-radius:4px;font-family:var(--mono);font-size:.8rem}
.ans{background:var(--soft);border:1px solid var(--line);border-radius:8px;padding:12px 16px;white-space:pre-wrap;font-size:.95rem}
.cause{padding:12px 0;border-top:1px solid var(--line)}
.badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.75rem;font-weight:800;color:var(--on-solid);background:var(--brand-solid)}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:8px 0 4px}.bar b{display:block;height:100%;background:var(--brand-solid)}
.evi span{display:inline-block;font-size:.75rem;padding:2px 8px;margin:4px 4px 0 0;border-radius:4px;border:1px solid var(--line);font-family:var(--mono)}
.tl{position:relative;padding-left:24px}.tl:before{content:"";position:absolute;left:8px;top:8px;bottom:8px;width:2px;background:var(--line)}
.ts{position:relative;margin:0 0 12px;font-size:.93rem}.ts:before{content:"";position:absolute;left:-20px;top:8px;width:12px;height:12px;border-radius:50%;background:inherit;border:3px solid var(--c)}
.risk{font-size:.75rem;font-weight:800;padding:2px 8px;border-radius:999px;color:var(--on-solid);background:var(--c)}
.muted{color:var(--muted);font-size:.82rem}
.apv{border:2px solid var(--warn);background:var(--warn-soft);border-radius:12px;padding:16px}
.diff{width:100%;border-collapse:collapse;font-size:.9rem}.diff td,.diff th{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.diff th{color:var(--muted);font-size:.8rem}.old{color:var(--bad);text-decoration:line-through}.new{color:var(--ok);font-weight:700}
.doc{border-bottom:1px solid var(--line);padding:8px 0;font-size:.82rem}
.doc b{font-family:var(--mono);color:var(--brand)}
.tr{font-size:.8rem;margin:0 0 4px;color:var(--muted)}.tr b{color:inherit}
.kv{display:grid;grid-template-columns:auto 1fr;gap:8px 12px;align-items:center;font-size:.82rem;color:var(--muted)}
.ico{width:16px;height:16px;color:var(--brand);display:block}
.foot{color:var(--muted);font-size:.75rem;text-align:center;padding:16px 0}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}
</style>""", unsafe_allow_html=True)

# ---------------- 상태 ----------------
ss = st.session_state
for k, v in {"resp": None, "before": None, "after": None, "question": "", "scenario": "S01", "demo": False, "decided": None}.items():
    ss.setdefault(k, v)
# [수정] 시나리오 선택·문의 입력칸은 key로 상태를 갖는 위젯이라, 코드에서 index·value를 바꿔도 화면이 따라오지 않았다
# (예시 문의를 불러와도 시나리오가 그대로였음). 바꿀 값은 _pending에 두고, 위젯을 그리기 전에 위젯 상태에 직접 넣는다.
ss.setdefault("scn_box", ss.scenario)
ss.setdefault("q_box", ss.question)
if "_pending" in ss:
    _q, _s = ss.pop("_pending")
    if _q is not None:
        ss.q_box = ss.question = _q
    if _s is not None:
        ss.scn_box = ss.scenario = _s


@st.cache_resource(show_spinner="검색 인덱스 준비 중... (처음 한 번)")
def _warm() -> int:
    from src.knowledge.retriever import warm_up
    return warm_up()


def call_agent(**kw) -> dict:
    _warm()   # [추가 구현] 실제 에이전트를 처음 부를 때 인덱스를 먼저 준비
    from src.workflow.entry import handle_query  # Bedrock 클라이언트는 실제 호출 때만 불러온다
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
from src.evaluation.cases import load_cases  # noqa: E402
rows = load_cases()   # id = 케이스 이름(P1…), 규약 3-4의 번호는 num
with st.sidebar:
    st.markdown("### 시연 도구")
    ss.demo = st.toggle("샘플 응답으로 보기 (Bedrock 호출 없음)", value=ss.demo)
    pick = st.selectbox("예시 문의 불러오기", ["(직접 입력)"] + [f"{r['id']}: {r['category']}" for r in rows])
    if st.button("불러오기", width="stretch") and pick != "(직접 입력)":
        r = rows[[f"{x['id']}: {x['category']}" for x in rows].index(pick)]
        ss.resp, ss.after, ss.decided = None, None, None
        m = re.search(r"scenario=(S\d\d)", r["note"])
        ss["_pending"] = (r["input"], m.group(1) if m else None)
        st.rerun()
    if st.button("처음부터", width="stretch"):
        ss.resp, ss.after, ss.decided = None, None, None
        st.rerun()
    st.caption("모든 테넌트와 메일 데이터는 가상입니다.")

# ---------------- 상단 바 ----------------
top_l, top_r = st.columns([5, 2])
with top_l:
    st.markdown("<div class='topbar'><div class='logo' aria-hidden='true'>GE</div><div><p class='wordmark'>Gemini Enterprise 설정 지원 에이전트</p>"
                "<p class='tagline'>근거 있는 진단, 승인 후 조치</p></div><span class='chip'>가상 테넌트: 가상상사</span></div>",
                unsafe_allow_html=True)
with top_r:
    scen = {k: f"{k}: {v['title']}" for k, v in tenant.SCENARIOS.items()}
    ss.scenario = st.selectbox("시나리오", list(scen), key="scn_box", format_func=scen.get,
                               help="예시 문의를 불러오면 짝지어 둔 시나리오로 함께 바뀝니다. 장애는 그래프 밖에서 이 시나리오로 주입됩니다 (D-2)")

tab_main, tab_eval = st.tabs(["진단", "평가 대시보드"])

with tab_main:
    resp = ss.resp
    stage = 1 if not resp else (4 if ss.decided else (3 if resp.get("approval_required") else 4))
    c_left, c_mid, c_right = st.columns([1.15, 4.2, 1.75], gap="medium")

    # ---- 좌측: 진행 단계 ----
    with c_left:
        with st.container(border=True):
            for n, (t, s) in enumerate([("문의 입력", "개인정보 자동 가림"), ("진단", "문서 검색과 테넌트 조회"),
                                        ("승인", "관리자가 결정"), ("결과", "바뀐 설정 확인")], 1):
                cls = "done" if n < stage else ("on" if n == stage else "")
                st.markdown(f"<div class='stp {cls}'><span class='no'>{n}</span><div>{t}<small>{s}</small></div></div>", unsafe_allow_html=True)

    # ---- 가운데 ----
    with c_mid:
        with st.container(border=True):
            st.markdown("<div class='sec'><span class='num'>1</span>문의 입력</div>", unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                ss.question = st.text_area("관리자 문의 (전달받은 메일이나 오류 메시지를 붙여넣기)", key="q_box", height=230)
            with b:
                h, kinds, inj = masked_html(ss.question)
                st.markdown("<div class='muted' style='margin-bottom:6px'>에이전트에 전달되는 내용 (마스킹 미리보기)</div>"
                            f"<div class='prev'>{h or '<span class=muted>입력을 기다리는 중</span>'}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='muted'>가린 종류: {', '.join(kinds) or '없음'}"
                            + (". <b style='color:var(--bad)'>붙여넣은 내용 속 지시를 탐지했고 따르지 않습니다.</b>" if inj else "") + "</div>",
                            unsafe_allow_html=True)
            run = st.button("진단 요청", type="primary")

        if run:
            if ss.demo:
                sample = json.loads((ROOT / "data" / "demo" / "sample_response.json").read_text(encoding="utf-8"))
                ss.resp = sample["response"]
                ss["_pending"] = (sample["question"], sample["scenario_id"])
                ss.before = tenant.initial_state(sample["scenario_id"])
            else:
                with st.spinner("문서를 검색하고 테넌트를 조회해 런북을 만드는 중…"):
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
                                    f"<div class='muted'>확신도 {c['confidence']:.0%}. {esc(c.get('reason', ''))}</div>"
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
                dec = "approve" if b1.button("승인 (approve)", type="primary", width="stretch") else (
                      "reject" if b2.button("거절 (reject)", width="stretch") else None)
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
            st.markdown("<div class='kv'><svg class='ico' viewBox='0 0 16 16' aria-hidden='true'><rect x='3' y='7' width='10' height='7' rx='1.5' fill='none' stroke='currentColor' stroke-width='1.5'/><path d='M5.5 7V5a2.5 2.5 0 0 1 5 0v2' fill='none' stroke='currentColor' stroke-width='1.5'/></svg><span>개인정보와 시크릿 마스킹</span><svg class='ico' viewBox='0 0 16 16' aria-hidden='true'><path d='M8 1.5 13.5 4v4c0 3-2.4 5.6-5.5 6.5C4.9 13.6 2.5 11 2.5 8V4z' fill='none' stroke='currentColor' stroke-width='1.5'/></svg><span>붙여넣은 내용 속 지시 무시</span><svg class='ico' viewBox='0 0 16 16' aria-hidden='true'><circle cx='8' cy='8' r='6.5' fill='none' stroke='currentColor' stroke-width='1.5'/><path d='M3.4 12.6 12.6 3.4' stroke='currentColor' stroke-width='1.5'/></svg><span>승인 없는 변경 금지</span><svg class='ico' viewBox='0 0 16 16' aria-hidden='true'><path d='M4 1.5h6l3 3v10H4z' fill='none' stroke='currentColor' stroke-width='1.5'/><path d='M6 8h5M6 11h5' stroke='currentColor' stroke-width='1.5'/></svg><span>근거 없으면 '확인 필요'</span></div>", unsafe_allow_html=True)

    st.markdown("<div class='foot'>테넌트와 메일 데이터는 모두 가상입니다. 근거 문서는 Gemini Enterprise 공식 문서(CC BY 4.0, 수집 2026-11-25)입니다."
                + (" 지금은 샘플 응답 모드입니다." if ss.demo else "") + "</div>", unsafe_allow_html=True)

# ================= 평가 대시보드 =================
with tab_eval:
    st.subheader("인-아웃 세트 평가 (18건)")
    ev = ROOT / "evaluation"
    rounds = {}
    for name, path in [("1차", ev / "round1_results.json"), ("2차", ev / "round2_results.json"), ("3차", ev / "round3_results.json"), ("4차", ev / "round4_results.json"), ("5차", ev / "round5_results.json"), ("6차", ev / "round6_results.json"), ("7차", ev / "round7_results.json"), ("8차", ev / "round8_results.json"), ("9차", ev / "round9_results.json"), ("10차", ev / "round10_results.json")]:
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
        for nm in ("2차", "3차", "4차", "5차", "6차", "7차", "8차", "9차", "10차"):
            if nm in rounds:
                src[nm] = rounds[nm]
        for name, res in src.items():
            for k in ["faithfulness", "answer_relevancy", "llm_context_precision_with_reference", "context_recall"]:
                vals = [r["ragas"][k] for r in res if r.get("ragas") and r["ragas"].get(k) is not None]
                if vals:
                    rag.append({"라운드": name, "지표": k, "평균": sum(vals) / len(vals)})
        if rag:
            st.markdown("**RAGAS 4지표** (positive와 edge, 채점 모델 Haiku 4.5 기준)")
            st.bar_chart(pd.DataFrame(rag), x="지표", y="평균", color="라운드", stack=False)
        last = list(rounds)[-1]
        st.markdown(f"**케이스별 결과 ({last})**")
        st.dataframe(pd.DataFrame([{"id": r["id"], "범주": r["category"], "준블라인드": "AI 작성" if r["semi_blind"] else "",
                                    "정답": r["expected_fault"], "1순위": r["top_fault"], "통과": "통과" if r["passed"] else "실패",
                                    "도구 일치": "일치" if r["tool_match"] else "불일치", "초": r["seconds"]} for r in rounds[last]]),
                     width="stretch", hide_index=True)
