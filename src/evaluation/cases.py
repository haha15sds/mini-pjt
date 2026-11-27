"""인-아웃 세트(evaluation/test_queries.csv) 읽기.

과제 규약(3-4)대로 id 는 1부터 매긴 번호이고, 보고서·결과 파일에서 쓰는 케이스 이름(P1, E2, G1 …)은
note 의 `case=` 값에 둔다. 읽을 때 row["id"] 를 케이스 이름으로, row["num"] 을 CSV 번호로 바꿔 준다.
expected_traits 에는 사람이 읽는 설명(한국어 문구)과 판정 규칙(`키:값`)이 함께 있다. 판정은 규칙만 쓴다.
"""
from __future__ import annotations

import csv
import re

from src.utils.paths import EVAL_DIR

RULE = re.compile(r"^[a-z_]+:")   # 판정 규칙 토큰(fault:F1, contains:…). 그 밖의 문구는 사람이 읽는 설명


def load_cases() -> list[dict]:
    rows = list(csv.DictReader(open(EVAL_DIR / "test_queries.csv", encoding="utf-8-sig")))
    for r in rows:
        case = next((p.split("=", 1)[1].strip() for p in r["note"].split(";") if p.strip().startswith("case=")), r["id"])
        r["num"], r["id"] = r["id"], case
    return rows


def rule_tokens(s: str) -> list[str]:
    """세미콜론으로 나눈 항목 중 판정 규칙만 돌려준다."""
    return [x.strip() for x in s.split(";") if RULE.match(x.strip())]
