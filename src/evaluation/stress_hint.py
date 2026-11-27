"""강사 힌트 집중 점검: 값 비교로 갈리는 원인(F4 대소문자·식별자, F5 그룹 클레임 한도)을 변형 20개로 시험한다.

- 모든 케이스는 똑같이 모호한 문의 한 통을 쓴다(증상 힌트 없음). recent_errors도 비운다.
  → 진단은 테넌트 값 비교로만 가능하다.
- checks(코드 계산)를 켠 경우와 끈 경우(DISABLE_CHECKS=1)를 각각 돌려 1순위 원인 일치율을 비교한다.
- 정식 인-아웃 세트(18건)와 별개의 점검이다. 결과: evaluation/stress_hint_report.md

실행: python src/evaluation/stress_hint.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[2]   # 저장소 루트
sys.path.insert(0, str(ROOT))   # src 패키지를 찾도록 저장소 루트를 경로에 넣는다
from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")
from src.workflow import entry as agent  # noqa: E402
from src import tenant  # noqa: E402
from src.knowledge.retriever import warm_up  # noqa: E402

MAIL = "안녕하세요, 가상상사 IT팀입니다.\n일부 직원이 Gemini Enterprise에서 SharePoint 문서가 검색되지 않는다고 합니다. 원인과 조치를 알려 주세요.\n\nIT팀 드림"
SAML = {"wif_mapping.provider": "Entra ID (SAML)"}
ALL = {"wif_mapping.group_claims_filter": "all_security_groups"}


def u(uid: str, **kv) -> dict:
    return {f"users[user_id={uid}].{k}": v for k, v in kv.items()}


# (id, 설명, patch, 정답으로 인정할 1순위 원인 집합)
CASES = [
    ("H01", "u03 이메일·식별자 대문자 시작", u("u03", email="Park.C@gasang.example", subject_seen="Park.C@gasang.example"), {"F4"}),
    ("H02", "u01 이메일·식별자 대문자 시작", u("u01", email="Kim.A@gasang.example", subject_seen="Kim.A@gasang.example"), {"F4"}),
    ("H03", "u02 식별자만 대문자(이메일은 소문자)", u("u02", subject_seen="LEE.B@gasang.example"), {"F4"}),
    ("H04", "u01 이메일 주소 변경(전 필드)", u("u01", email="kim.aa@gasang.example", upn="kim.aa@gasang.example", subject_seen="kim.aa@gasang.example"), {"F4"}),
    ("H05", "u02 이메일 주소 변경(전 필드)", u("u02", email="lee.b2@gasang.example", upn="lee.b2@gasang.example", subject_seen="lee.b2@gasang.example"), {"F4"}),
    ("H06", "u01 식별자 전부 대문자", u("u01", email="KIM.A@GASANG.EXAMPLE", subject_seen="KIM.A@GASANG.EXAMPLE"), {"F4"}),
    ("H07", "OIDC u02 그룹 201개(한도 200 초과)", {**ALL, **u("u02", group_count=201)}, {"F5"}),
    ("H08", "OIDC u02 그룹 230개", {**ALL, **u("u02", group_count=230)}, {"F5"}),
    ("H09", "OIDC u01 그룹 450개", {**ALL, **u("u01", group_count=450)}, {"F5"}),
    ("H10", "OIDC u03 210개·u01 205개", {**ALL, **u("u03", group_count=210), **u("u01", group_count=205)}, {"F5"}),
    ("H11", "SAML u02 그룹 151개(한도 150 초과)", {**SAML, **ALL, **u("u02", group_count=151)}, {"F5"}),
    ("H12", "SAML u02 그룹 180개", {**SAML, **ALL, **u("u02", group_count=180)}, {"F5"}),
    ("H13", "대조: OIDC u02 그룹 199개(한도 안)", {**ALL, **u("u02", group_count=199)}, {"none"}),
    ("H14", "대조: SAML u02 그룹 149개(한도 안)", {**SAML, **ALL, **u("u02", group_count=149)}, {"none"}),
    ("H15", "대조: u02 230개지만 '앱에 할당된 그룹'만 보내도록 제한됨", u("u02", group_count=230), {"none"}),
    ("H16", "대조: 정상 테넌트", {}, {"none"}),
    ("H17", "대조: OIDC u02 그룹 정확히 200개(초과 아님)", {**ALL, **u("u02", group_count=200)}, {"none"}),
    ("H18", "복합: u03 대소문자 + u02 230개", {**ALL, **u("u02", group_count=230), **u("u03", email="Park.C@gasang.example", subject_seen="Park.C@gasang.example")}, {"F4", "F5"}),
    ("H19", "u03 이메일 주소 변경(전 필드)", u("u03", email="park.cy@gasang.example", upn="park.cy@gasang.example", subject_seen="park.cy@gasang.example"), {"F4"}),
    ("H20", "SAML u03 그룹 300개", {**SAML, **ALL, **u("u03", group_count=300)}, {"F5"}),
]


def register() -> None:
    for cid, title, patch, _ in CASES:
        tenant.SCENARIOS[cid] = {"scenario_id": cid, "title": title,
                                 "inject": [{"fault_id": "stress", "patch": {**patch, "recent_errors": []}}],
                                 "expected_fault_id": "stress"}


def top(res: dict) -> str:
    real = [c for c in (res.get("diagnosis") or {}).get("causes", []) if c["fault_id"] != "none"]
    return real[0]["fault_id"] if real else "none"


def run(mode: str) -> list[dict]:
    os.environ["DISABLE_CHECKS"] = "1" if mode == "checks 끔" else "0"
    out = []
    for cid, title, _, ok in CASES:
        t0 = time.time()
        r = agent.handle_query(MAIL, scenario_id=cid)
        if "ThrottlingException" in r.get("answer", ""):
            sys.exit("Bedrock 한도 - 중단")
        t = top(r)
        out.append({"id": cid, "title": title, "expected": sorted(ok), "top": t, "hit": t in ok, "sec": round(time.time() - t0, 1)})
        print(f"[{mode}] {cid} 정답 {sorted(ok)} 1순위 {t} {'O' if t in ok else 'X'} {out[-1]['sec']}s", flush=True)
    return out


def main() -> None:
    register()
    agent.reset_checkpoints()
    print("인덱스:", warm_up())
    on = run("checks 켬")
    # [중간평가 반영] 전에는 ONLY_ON=1 이면 off = on 이라 '끔' 열에 켠 조건 점수가 그대로 찍혔다(차이 0이 효과 없음처럼 보임).
    #  대조 실험을 생략하면 '끔' 열은 '-'로 두고, 손으로 정리한 3조건 보고서(stress_hint_report.md)를 덮어쓰지 않는다.
    only_on = os.getenv("ONLY_ON") == "1"
    off = None if only_on else run("checks 끔")
    (ROOT / "evaluation" / "stress_hint_results.json").write_text(
        json.dumps({"checks_on": on, "checks_off": off}, ensure_ascii=False, indent=1), encoding="utf-8")
    groups = {"F4 식별자(6+1)": [c[0] for c in CASES if c[3] == {"F4"}], "F5 그룹 한도(7)": [c[0] for c in CASES if c[3] == {"F5"}],
              "대조군 none(5)": [c[0] for c in CASES if c[3] == {"none"}], "복합(1)": ["H18"]}
    L = ["# 강사 힌트 집중 점검 — 값 비교 원인 변형 20개", "",
         "모든 케이스에 같은 모호한 문의를 쓰고 오류 문구(recent_errors)를 비워, 테넌트 값 비교만으로 원인을 찾게 했다.", "",
         "| 묶음 | checks 켬 | checks 끔 |", "|---|---|---|"]
    for g, ids in groups.items():
        a = sum(x["hit"] for x in on if x["id"] in ids)
        b = "-" if off is None else f"{sum(x['hit'] for x in off if x['id'] in ids)} / {len(ids)}"
        L.append(f"| {g} | {a} / {len(ids)} | {b} |")
    tot_off = "-" if off is None else f"{sum(x['hit'] for x in off)} / 20"
    L.append(f"| **전체** | **{sum(x['hit'] for x in on)} / 20** | **{tot_off}** |")
    L += ["", "| id | 변형 | 정답 | checks 켬 | checks 끔 |", "|---|---|---|---|---|"]
    for i, a in enumerate(on):
        b = "-" if off is None else f"{off[i]['top']} {'✅' if off[i]['hit'] else '❌'}"
        L.append(f"| {a['id']} | {a['title']} | {', '.join(a['expected'])} | {a['top']} {'✅' if a['hit'] else '❌'} | {b} |")
    # 저장된 stress_hint_report.md 는 세 조건(①②③)을 손으로 합친 문서라 덮어쓰지 않는다
    name = "stress_hint_report_only_on.md" if only_on else "stress_hint_report_run.md"
    (ROOT / "evaluation" / name).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("done", sum(x["hit"] for x in on), tot_off, "->", name)


if __name__ == "__main__":
    main()
