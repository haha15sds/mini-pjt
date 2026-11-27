"""LLM 클라이언트 설정 (AWS Bedrock). 진단 에이전트·평가 스크립트가 함께 쓴다."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_aws import ChatBedrockConverse

from src.utils.paths import ROOT

load_dotenv(ROOT / ".env")

MODEL_MAIN = os.getenv("MODEL_MAIN", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
MODEL_FAST = os.getenv("MODEL_FAST", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

llm_main = ChatBedrockConverse(model=MODEL_MAIN, region_name=REGION, temperature=0)
llm_fast = ChatBedrockConverse(model=MODEL_FAST, region_name=REGION, temperature=0)


# [추가 구현] 같은 모델을 global 교차 리전 추론 프로필로도 만들어 둔다. us 프로필이 한도(ThrottlingException)에
# 걸리면 같은 모델을 다른 리전 용량으로 다시 부른다(모델이 같으므로 1차·2차 비교가 유지된다).
def _global(model_id: str) -> str:
    return "global." + model_id.split(".", 1)[1] if model_id.startswith("us.") else model_id


llm_main_g = ChatBedrockConverse(model=_global(MODEL_MAIN), region_name=REGION, temperature=0)
llm_fast_g = ChatBedrockConverse(model=_global(MODEL_FAST), region_name=REGION, temperature=0)
