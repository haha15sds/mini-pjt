"""불일치 점검(M 세트): 문의 증상과 테넌트 상태가 어긋날 때 에이전트가 어떻게 답하는지 측정한다.

정식 인-아웃 세트(18건)의 문의 글을 그대로 쓰고, 시나리오만 다른 장애로 바꿔 짝짓는다.
바람직한 답: 테넌트에서 보이는 실제 문제는 알리되, 문의 증상과 맞지 않는다는 사실을 밝히고 단정하지 않는다.

판정(문자열·구조 규칙, LLM 판사 아님)
- 좋음   : 테넌트의 실제 장애를 원인 후보에 올리고, 답변에 불일치·확인 필요를 밝힘
- 단정   : 테넌트의 장애를 1순위로 확신도 0.6 넘게 내놓으면서 불일치를 밝히지 않음
- 숨김   : 원인 후보가 없고 테넌트의 실제 장애도 언급하지 않음
- 지어냄 : 테넌트에 없는 장애(문의 증상의 장애)를 원인으로 내놓음
- 오진   : 테넌트의 실제 장애도, 증상의 장애도 아닌 후보를 냄

`--rejudge` : 저장된 mismatch_results.json 을 다시 실행하지 않고 지금 판정 기준으로 다시 판정한다

실행: python src/evaluation/mismatch_check.py   → evaluation/mismatch_report.md
"""
from __future__ import annotations

import json
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
from src.evaluation.cases import load_cases  # noqa: E402

# (id, 문의 케이스, 문의 증상의 장애, 바꿔 낀 시나리오, 그 시나리오의 실제 장애)
CASES = [
    ("M01", "P6", "F5", "S04", "F6"),
    ("M02", "P1", "F1", "S06", "F5"),
    ("M03", "P4", "F6", "S03", "F4"),
    ("M04", "P3", "F4", "S02", "F2"),
    ("M05", "P2", "F2", "S05", "F3"),
    ("M06", "P5", "F3", "S07", "F4"),
    ("M07", "P7", "F1", "S04", "F6"),
    ("M08", "E3", "F4", "S06", "F5"),
]
FLAG = ["맞지 않", "일치하지 않", "부합하지 않", "설명하지 못", "설명되지 않", "관련이 없", "직접 관련", "확인 필요", "추가 확인", "별도의", "다른 원인"]


def judge(res: dict, symptom_fault: str, tenant_fault: str) -> dict:
    causes = [c for c in (res.get("diagnosis") or {}).get("causes", []) if c["fault_id"] != "none"]
    ids = [c["fault_id"] for c in causes]
    answer = res.get("answer", "")
    flagged = any(k in answer for k in FLAG)
    top = causes[0] if causes else None
    pa = (res.get("pending_action") or {}).get("fix_id")
    fix_ok = pa is None or tenant.FIXES.get(pa, {}).get("fault_id") == tenant_fault   # 승인 카드의 조치가 실제 장애의 조치인가
    if symptom_fault in ids and symptom_fault != tenant_fault:
        verdict = "지어냄"
    elif tenant_fault in ids and flagged and fix_ok:
        verdict = "좋음"
    elif tenant_fault in ids and flagged:
        verdict = "조치 어긋남"
    elif top and top["fault_id"] == tenant_fault and top["confidence"] > 0.6 and not flagged:
        verdict = "단정"
    elif not causes and tenant_fault not in answer:
        verdict = "숨김"
    elif tenant_fault in ids:
        verdict = "단정"
    else:
        # [중간평가 반영] 전에는 여기서 '추가 확인' 같은 표현만 있으면 '좋음'이었다. 실제 장애도 증상 장애도 아닌
        # 후보를 낸 경우는 오진이고, 후보가 없으면 실제 문제를 알리지 않은 것(숨김)이다.
        verdict = "오진" if causes else "숨김"
    return {"causes": ids, "top_conf": round(top["confidence"], 2) if top else None, "flagged": flagged, "fix": pa, "fix_ok": fix_ok, "verdict": verdict}


def main() -> None:
    rows = {r["id"]: r for r in load_cases()}
    agent.reset_checkpoints()
    print("인덱스:", warm_up(), flush=True)
    out = []
    for mid, qid, sf, sid, tf in CASES:
        t0 = time.time()
        res = agent.handle_query(rows[qid]["input"], scenario_id=sid)
        if "ThrottlingException" in res.get("answer", ""):
            sys.exit("Bedrock 한도 - 중단")
        j = judge(res, sf, tf)
        out.append({"id": mid, "query": qid, "symptom_fault": sf, "scenario": sid, "tenant_fault": tf, **j,
                    "answer": res.get("answer", ""), "sec": round(time.time() - t0, 1)})
        print(f"{mid} {qid}(증상 {sf}) + {sid}(실제 {tf}) → 원인 {j['causes']} 확신 {j['top_conf']} 불일치표시 {j['flagged']} 조치 {j['fix']} → {j['verdict']}", flush=True)
    (ROOT / "evaluation" / "mismatch_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    write_report(out)


def rejudge() -> None:
    """저장된 결과를 지금 판정 기준으로 다시 판정한다 (Bedrock 호출 없음)."""
    path = ROOT / "evaluation" / "mismatch_results.json"
    out = json.loads(path.read_text(encoding="utf-8"))
    for o in out:
        causes = [{"fault_id": f, "confidence": (o["top_conf"] or 0) if i == 0 else 0} for i, f in enumerate(o["causes"])]
        res = {"diagnosis": {"causes": causes}, "answer": o["answer"], "pending_action": {"fix_id": o["fix"]} if o["fix"] else None}
        o.update(judge(res, o["symptom_fault"], o["tenant_fault"]))
        print(o["id"], o["verdict"])
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    cnt = {k: sum(o["verdict"] == k for o in out) for k in ("좋음", "조치 어긋남", "단정", "숨김", "지어냄", "오진")}
    print("재판정", cnt, "(보고서 mismatch_report.md 는 손으로 정리한 회차 비교가 있어 덮어쓰지 않는다)")


def write_report(out: list[dict]) -> None:
    cnt = {k: sum(o["verdict"] == k for o in out) for k in ("좋음", "조치 어긋남", "단정", "숨김", "지어냄", "오진")}
    L = ["# 불일치 점검 (M 세트) — 문의 증상과 테넌트 상태가 어긋날 때", "",
         "정식 18건의 문의 글을 그대로 쓰고 시나리오만 다른 장애로 바꿔 짝지었다. 정식 평가와 별개다.", "",
         f"**결과: 좋음 {cnt['좋음']} · 조치 어긋남 {cnt['조치 어긋남']} · 단정 {cnt['단정']} · 숨김 {cnt['숨김']} · 지어냄 {cnt['지어냄']} · 오진 {cnt['오진']} (총 {len(out)})**", "",
         "| id | 문의(증상 장애) | 시나리오(실제 장애) | 원인 후보 | 1순위 확신도 | 불일치 표시 | 승인 카드 조치 | 판정 |", "|---|---|---|---|---|---|---|---|"]
    for o in out:
        L.append(f"| {o['id']} | {o['query']} ({o['symptom_fault']}) | {o['scenario']} ({o['tenant_fault']}) | {', '.join(o['causes']) or '-'} | "
                 f"{o['top_conf'] if o['top_conf'] is not None else '-'} | {'예' if o['flagged'] else '아니오'} | {o['fix'] or '-'} | {o['verdict']} |")
    L += ["", "판정 기준: 좋음 = 실제 장애를 알리고 불일치·확인 필요를 밝히며 승인 카드 조치도 실제 장애의 것 / 조치 어긋남 = 진단은 맞지만 승인 카드에 다른 장애의 조치가 뜸 / 단정 = 실제 장애를 확신 있게 원인으로 단정 / "
          "숨김 = 실제 장애를 알리지 않음 / 지어냄 = 테넌트에 없는 장애를 원인으로 냄 / 오진 = 실제 장애도 증상 장애도 아닌 후보를 냄"]
    (ROOT / "evaluation" / "mismatch_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("done", cnt)


if __name__ == "__main__":
    rejudge() if "--rejudge" in sys.argv else main()
