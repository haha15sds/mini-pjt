"""프로젝트 경로 (여러 도메인이 함께 쓰는 공통 설정)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]   # 저장소 루트 (src/utils/paths.py 기준 두 단계 위)
DATA_DIR = ROOT / "data"
EVAL_DIR = ROOT / "evaluation"               # 평가 입력(test_queries.csv)과 결과(보고서·JSON)를 두는 곳
