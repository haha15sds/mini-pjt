"""[추가 구현] 반복 실행 편차 집계: 같은 코드로 18건을 3번 돌린 결과를 모아 중앙값·범위를 낸다.

한 번 실행한 RAGAS 점수는 실행마다 흔들려서(예: 6~9차 P6 faithfulness 0.87→0.67→0.53→1.00)
라운드 간 작은 차이가 개선인지 편차인지 구분할 수 없었다. 개선 전(9차 코드)과 개선 후(원인 중심 재검색)를
각각 3번씩 돌려 비교한다.

실행: python src/evaluation/repeat_summary.py   → evaluation/repeat_report.md
"""
from __future__ import annotations

import json
import statistics as stt
from pathlib import Path

EV = Path(__file__).resolve().parents[2] / "evaluation"   # 결과 파일은 저장소 루트의 evaluation/
GROUPS = {
    "개선 전 (9차 코드)": [EV / "round9_results.json", EV / "repeat/before_r2/round9_results.json", EV / "repeat/before_r3/round9_results.json"],
    "개선 후 (원인 중심 재검색)": [EV / f"repeat/after_r{i}/round10_results.json" for i in (1, 2, 3)],
}
KEYS = [("faithfulness", "faithfulness"), ("answer_relevancy", "answer_relevancy"),
        ("llm_context_precision_with_reference", "context_precision"), ("context_recall", "context_recall")]


def load(p: Path) -> list[dict]:
    # 동시 실행 중 RAGAS 채점이 한도·시간 초과로 빠진 회차는 혼자 다시 채점한 _rescored 파일을 쓴다(에이전트 답은 같음)
    rs = p.with_name(p.stem + "_rescored.json")
    d = json.loads((rs if rs.exists() else p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["results"]


def run_stats(rows: list[dict]) -> dict:
    out = {"pass": sum(r["passed"] for r in rows), "n": len(rows),
           "ac4": sum(r["top_fault"] == r["expected_fault"] for r in rows if r["category"] == "positive")}
    for k, _ in KEYS:
        vals = [r["ragas"][k] for r in rows if r.get("ragas") and r["ragas"].get(k) is not None]
        out[k] = sum(vals) / len(vals) if vals else None
        out[k + "_n"] = len(vals)
    return out


def fmt(vals: list[float]) -> str:
    vals = [v for v in vals if v is not None]
    return f"{stt.median(vals):.3f} ({min(vals):.3f}~{max(vals):.3f})" if vals else "-"


def main() -> None:
    runs = {g: [load(p) for p in ps if p.exists()] for g, ps in GROUPS.items()}
    stats = {g: [run_stats(r) for r in rs] for g, rs in runs.items()}
    names = list(GROUPS)
    L = ["# 반복 실행 편차와 검색 개선 효과", "",
         "같은 코드로 18건을 3번씩 돌렸다. 값은 **중앙값 (최소~최대)**. RAGAS 채점 모델 Claude Haiku 4.5, positive·edge 11건 평균.", "",
         "| 항목 | " + " | ".join(names) + " |", "|---|" + "---|" * len(names)]
    L.append("| 실행 횟수 | " + " | ".join(str(len(stats[g])) for g in names) + " |")
    L.append("| 통과 (18건) | " + " | ".join(", ".join(f"{s['pass']}/{s['n']}" for s in stats[g]) for g in names) + " |")
    L.append("| AC-4 1순위 원인 (positive 7건) | " + " | ".join(", ".join(f"{s['ac4']}/7" for s in stats[g]) for g in names) + " |")
    for k, label in KEYS:
        L.append(f"| {label} | " + " | ".join(fmt([s[k] for s in stats[g]]) for g in names) + " |")
    miss = {g: sum(11 * 4 - sum(s[k + "_n"] for k, _ in KEYS) for s in stats[g]) for g in names}
    L += ["", f"- RAGAS 채점 시간 초과로 빠진 값: " + ", ".join(f"{g} {miss[g]}개" for g in names) + " (평균에서 제외)", ""]
    # 케이스별 평균 비교
    L += ["## 케이스별 평균 (3회)", "", "| id | 정답 | context_precision 전 → 후 | faithfulness 전 → 후 |", "|---|---|---|---|"]
    ids = [r["id"] for r in runs[names[0]][0] if r.get("ragas")]
    for cid in ids:
        cells = []
        for k in ("llm_context_precision_with_reference", "faithfulness"):
            m = []
            for g in names:
                v = [r["ragas"].get(k) for rs in runs[g] for r in rs if r["id"] == cid and r.get("ragas") and r["ragas"].get(k) is not None]
                m.append(f"{sum(v) / len(v):.2f}" if v else "-")
            cells.append(" → ".join(m))
        exp = next(r["expected_fault"] for r in runs[names[0]][0] if r["id"] == cid)
        L.append(f"| {cid} | {exp} | {cells[0]} | {cells[1]} |")
    (EV / "repeat_report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
