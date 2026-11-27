"""LLM 클라이언트 설정 (AWS Bedrock). 진단 에이전트·평가 스크립트가 함께 쓴다."""
from __future__ import annotations

import os

from botocore.config import Config
from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

from src.utils.paths import ROOT

load_dotenv(ROOT / ".env")

MODEL_MAIN = os.getenv("MODEL_MAIN", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
MODEL_FAST = os.getenv("MODEL_FAST", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
CALL_TIMEOUT_S = 45   # [중간평가 반영] 모델 호출 1회의 응답 대기 상한. 전에는 ReAct 루프(60초)만 상한이 있고 분석·진단 호출은 무제한이었다
_CFG = Config(connect_timeout=10, read_timeout=CALL_TIMEOUT_S, retries={"max_attempts": 2, "mode": "standard"})

llm_main = ChatBedrockConverse(model=MODEL_MAIN, region_name=REGION, temperature=0, config=_CFG)
llm_fast = ChatBedrockConverse(model=MODEL_FAST, region_name=REGION, temperature=0, config=_CFG)


# [추가 구현] 같은 모델을 global 교차 리전 추론 프로필로도 만들어 둔다. us 프로필이 한도(ThrottlingException)에
# 걸리면 같은 모델을 다른 리전 용량으로 다시 부른다(모델이 같으므로 1차·2차 비교가 유지된다).
def _global(model_id: str) -> str:
    return "global." + model_id.split(".", 1)[1] if model_id.startswith("us.") else model_id


llm_main_g = ChatBedrockConverse(model=_global(MODEL_MAIN), region_name=REGION, temperature=0, config=_CFG)
llm_fast_g = ChatBedrockConverse(model=_global(MODEL_FAST), region_name=REGION, temperature=0, config=_CFG)
